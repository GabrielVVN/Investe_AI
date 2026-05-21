import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import numpy_financial as npf

app = Flask(__name__)
app.secret_key = 'chave_secreta_investe_ai'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investe_ai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS DE BANCO DE DADOS ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

class Configuracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    meta = db.Column(db.Float, default=100000.0) 
    saldo_inicial = db.Column(db.Float, default=0.0) 
    data_alvo = db.Column(db.Date, default=date(2030, 1, 1)) 
    rentabilidade_anual = db.Column(db.Float, default=0.10) 
    aporte_mensal_planejado = db.Column(db.Float, default=500.0)

class Aporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, default=datetime.utcnow)
    categoria = db.Column(db.String(50), nullable=False)
    ativo = db.Column(db.String(50), nullable=True)

# --- FILTRO PARA MOEDA BRASILEIRA (R$ XX.XXX,XX) ---
@app.template_filter('brl')
def formata_moeda(valor):
    if valor is None: valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_brl_number(s):
    """Parse a number string in Brazilian format (e.g. '1.234,56' or '1234,56' or '1234.56') to float.
    Accepts numeric types as well and returns float. Returns 0.0 for empty/None.
    """
    if s is None:
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    try:
        s = str(s).strip()
        if s == '':
            return 0.0
        # If contains comma as decimal separator, treat as Brazilian format
        if ',' in s and s.count(',') == 1 and '.' in s:
            # likely '1.234,56' -> remove dots, replace comma with dot
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s and '.' not in s:
            # '1234,56' -> replace comma with dot
            s = s.replace(',', '.')
        # else keep as is (e.g., '1234.56' or '1000')
        return float(s)
    except Exception:
        return 0.0

with app.app_context():
    db.create_all()

@app.before_request
def checar_autenticacao():
    rotas_livres = ['login', 'cadastro', 'static']
    if request.endpoint not in rotas_livres and 'user_id' not in session:
        return redirect(url_for('login'))

@app.route('/')
def index():
    user_id = session['user_id']
    config = Configuracao.query.filter_by(user_id=user_id).first()
    if not config:
        config = Configuracao(user_id=user_id)
        db.session.add(config)
        db.session.commit()

    aportes = Aporte.query.filter_by(user_id=user_id).order_by(Aporte.data.desc()).all()
    total_aportado = sum(a.valor for a in aportes)
    saldo_atual = config.saldo_inicial + total_aportado

    # Prepare display-friendly aporte entries (server-side formatted strings)
    aportes_display = []
    for a in aportes:
        aportes_display.append({
            'id': a.id,
            'user_id': a.user_id,
            'valor': a.valor,
            'valor_str': formata_moeda(a.valor),
            'data': a.data,
            'data_str': a.data.strftime('%d/%m/%Y') if hasattr(a.data, 'strftime') else str(a.data),
            'categoria': a.categoria,
            'ativo': a.ativo
        })
    
    distribuicao = {'Ações': 0, 'FIIs': 0, 'Renda Fixa': 0, 'Cripto': 0}
    for a in aportes:
        cat = 'Renda Fixa' if a.categoria == 'Tesouro' else a.categoria
        distribuicao[cat] = distribuicao.get(cat, 0) + a.valor

    # --- LÓGICA DO COACH FINANCEIRO ---
    hoje = datetime.now().date()
    taxa_mensal = (1 + config.rentabilidade_anual) ** (1/12) - 1
    
    # Calcular data prevista baseada no aporte atual
    data_alvo_str = config.data_alvo.strftime('%d/%m/%Y')
    prazo_str = config.data_alvo.strftime('%m/%Y')
    aporte_atual_str = formata_moeda(config.aporte_mensal_planejado)

    # Calcular aporte necessário para o prazo original
    meses_restantes_prazo = (config.data_alvo.year - hoje.year) * 12 + (config.data_alvo.month - hoje.month)
    if meses_restantes_prazo <= 0: meses_restantes_prazo = 1
    aporte_ideal = -npf.pmt(taxa_mensal, meses_restantes_prazo, -saldo_atual, config.meta)

    try:
        if saldo_atual >= config.meta:
            previsao_str = "Meta já atingida!"
            status = "success"
            msg_coach = "Parabéns! Sua meta já foi atingida com o saldo atual."
        elif config.aporte_mensal_planejado > 0:
            n_meses = npf.nper(taxa_mensal, -config.aporte_mensal_planejado, -saldo_atual, config.meta)
            if n_meses is None or n_meses != n_meses or n_meses == float('inf') or n_meses <= 0:
                previsao_str = "Projeção indisponível"
                status = "warning"
                msg_coach = (
                    f"Aporte atual de {aporte_atual_str}/mês não permite projetar a meta. "
                    f"Para chegar em {prazo_str}, você precisaria investir {formata_moeda(aporte_ideal)}/mês."
                )
            else:
                data_prevista = hoje + timedelta(days=int(n_meses * 30.44))
                previsao_str = data_prevista.strftime('%d/%m/%Y')
                if data_prevista <= config.data_alvo:
                    status = "success"
                    msg_coach = (
                        f"Excelente! Mantendo {aporte_atual_str}/mês, você atingirá a meta em {previsao_str}, "
                        f"antes do prazo ({prazo_str})."
                    )
                else:
                    status = "warning"
                    msg_coach = (
                        f"Com {aporte_atual_str}/mês você deve atingir a meta em {previsao_str}, "
                        f"após o prazo de {prazo_str}. Para cumprir o prazo, aporte {formata_moeda(aporte_ideal)}/mês."
                    )
        else:
            previsao_str = "Indeterminada (Ajuste seu aporte)"
            status = "warning"
            msg_coach = (
                f"Insira um aporte mensal maior que zero para calcular a data prevista. "
                f"Para atingir em {prazo_str}, você precisa investir {formata_moeda(aporte_ideal)}/mês."
            )
    except Exception:
        previsao_str = "Cálculo indisponível"
        status = "warning"
        msg_coach = (
            "O coach não conseguiu gerar a projeção. Verifique seus valores e tente novamente."
        )

    progresso_percentual = min((saldo_atual / config.meta) * 100, 100) if config.meta > 0 else 0
    saldo_atual_str = formata_moeda(saldo_atual)
    meta_str = formata_moeda(config.meta)

    return render_template('index.html', 
                           config=config, aportes=aportes_display, saldo_atual=saldo_atual, 
                           saldo_atual_str=saldo_atual_str, meta_str=meta_str,
                           aporte_atual_str=aporte_atual_str,
                           progresso_percentual=progresso_percentual, status=status, 
                           msg_coach=msg_coach, previsao_str=previsao_str, distribuicao=distribuicao)

@app.route('/investir', methods=['GET', 'POST'])
def investir():
    if request.method == 'POST':
        novo_aporte = Aporte(
            user_id=session['user_id'],
            categoria=request.form['categoria'],
            ativo=request.form.get('ativo', '').upper(),
            valor=parse_brl_number(request.form['valor'])
        )
        db.session.add(novo_aporte)
        db.session.commit()
        flash(f"Investimento de {formata_moeda(novo_aporte.valor)} registrado!", 'success')
        return redirect(url_for('index'))
    return render_template('investir.html')

@app.route('/deletar_aporte/<int:id>', methods=['POST'])
def deletar_aporte(id):
    aporte = Aporte.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(aporte)
    db.session.commit()
    flash('Investimento removido.', 'success')
    return redirect(url_for('index'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        if Usuario.query.filter_by(username=request.form['username']).first():
            flash('Usuário já existe.', 'error')
            return redirect(url_for('cadastro'))
        novo = Usuario(nome=request.form['nome'], username=request.form['username'], 
                       senha=generate_password_hash(request.form['senha']))
        db.session.add(novo)
        db.session.commit()
        flash('Conta criada!', 'success')
        return redirect(url_for('login'))
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        u = Usuario.query.filter_by(username=request.form['username']).first()
        if u and check_password_hash(u.senha, request.form['senha']):
            session.update({'user_id': u.id, 'username': u.username, 'nome': u.nome})
            return redirect(url_for('index'))
        flash('Credenciais inválidas.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    u = Usuario.query.get(session['user_id'])
    c = Configuracao.query.filter_by(user_id=session['user_id']).first()
    if request.method == 'POST':
        u.nome = request.form.get('nome')
        if request.form.get('senha'): u.senha = generate_password_hash(request.form.get('senha'))
        c.meta = parse_brl_number(request.form.get('meta'))
        c.aporte_mensal_planejado = parse_brl_number(request.form.get('aporte_mensal'))
        data_str = request.form.get('data_alvo')
        if data_str: c.data_alvo = datetime.strptime(data_str, '%Y-%m-%d').date()
        db.session.commit()
        flash('Perfil atualizado!', 'success')
        return redirect(url_for('perfil'))
    # provide formatted display strings for template (do not replace numeric inputs)
    meta_str = formata_moeda(c.meta)
    aporte_str = formata_moeda(c.aporte_mensal_planejado)
    data_alvo_str = c.data_alvo.strftime('%d/%m/%Y') if c.data_alvo else ''
    return render_template('perfil.html', user=u, config=c, meta_str=meta_str, aporte_str=aporte_str, data_alvo_str=data_alvo_str)

@app.route('/simulador', methods=['GET', 'POST'])
def simulador():
    if request.method == 'POST':
        try:
            val = parse_brl_number(request.form['valor'])
            p = request.form['perfil']
            dist = {'Conservador': {'Renda Fixa': 0.6, 'FIIs': 0.25, 'Ações': 0.15},
                    'Moderado': {'Renda Fixa': 0.4, 'FIIs': 0.3, 'Ações': 0.3},
                    'Agressivo': {'Renda Fixa': 0.2, 'FIIs': 0.3, 'Ações': 0.5}}[p]
            sim = {
                'data': date.today().strftime("%d/%m/%Y"),
                'valor_investido': val,
                'perfil': p,
                'distribuicao_percentual': dist,
                'valores_reais': {k: v * val for k, v in dist.items()}
            }
            # Server-side formatted strings for display
            sim['valor_investido_str'] = formata_moeda(val)
            sim['valores_reais_str'] = {k: formata_moeda(v * val) for k, v in dist.items()}
            return render_template('resultado.html', sim=sim)
        except: return redirect(url_for('simulador'))
    return render_template('simulador.html')

@app.route('/aprender')
def aprender():
    return render_template('aprender.html')

if __name__ == '__main__':
    app.run()