# app.py
import os
from datetime import datetime, date
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
    
    distribuicao = {'Ações': 0, 'FIIs': 0, 'Renda Fixa': 0, 'Cripto': 0}
    for a in aportes:
        cat = 'Renda Fixa' if a.categoria == 'Tesouro' else a.categoria
        if cat in distribuicao:
            distribuicao[cat] += a.valor
        else:
            distribuicao[cat] = a.valor

    hoje = datetime.now().date()
    meses_restantes = (config.data_alvo.year - hoje.year) * 12 + (config.data_alvo.month - hoje.month)
    if meses_restantes <= 0: meses_restantes = 1
    
    taxa_mensal = (1 + config.rentabilidade_anual) ** (1/12) - 1
    aporte_necessario = -npf.pmt(taxa_mensal, meses_restantes, -saldo_atual, config.meta)
    gap_aporte = aporte_necessario - config.aporte_mensal_planejado

    # MENSAGEM INTELIGENTE DO COACH
    status = "success"
    msg_coach = "No Alvo! O seu plano de aportes atual é suficiente para atingir a meta no prazo estabelecido."
    if gap_aporte > 0:
        status = "warning"
        msg_coach = f"Atenção: Para atingir a meta de R$ {config.meta:.2f} até {config.data_alvo.year}, o aporte ideal é R$ {aporte_necessario:.2f}/mês. Como seu plano atual é R$ {config.aporte_mensal_planejado:.2f}, tente ajustar o orçamento ou revise sua meta no Perfil!"

    progresso_percentual = min((saldo_atual / config.meta) * 100, 100) if config.meta > 0 else 0

    return render_template('index.html', 
                           config=config,
                           aportes=aportes, 
                           saldo_atual=saldo_atual, 
                           meses_restantes=meses_restantes,
                           progresso_percentual=progresso_percentual,
                           status=status,
                           msg_coach=msg_coach,
                           distribuicao=distribuicao)

@app.route('/investir', methods=['GET', 'POST'])
def investir():
    if request.method == 'POST':
        novo_aporte = Aporte(
            user_id=session['user_id'],
            categoria=request.form['categoria'],
            ativo=request.form.get('ativo', '').upper(),
            valor=float(request.form['valor'])
        )
        db.session.add(novo_aporte)
        db.session.commit()
        
        flash(f"Investimento de R$ {novo_aporte.valor:.2f} registado com sucesso!", 'success')
        return redirect(url_for('index'))
        
    return render_template('investir.html')

@app.route('/deletar_aporte/<int:id>', methods=['POST'])
def deletar_aporte(id):
    aporte = Aporte.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(aporte)
    db.session.commit()
    flash('Investimento removido do seu histórico.', 'success')
    return redirect(url_for('index'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        if Usuario.query.filter_by(username=username).first():
            flash('Utilizador já existe.', 'error')
            return redirect(url_for('cadastro'))
            
        novo_usuario = Usuario(
            nome=request.form['nome'],
            username=username,
            senha=generate_password_hash(request.form['senha'])
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Conta criada! Faça o seu login.', 'success')
        return redirect(url_for('login'))
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        usuario = Usuario.query.filter_by(username=request.form['username']).first()
        if usuario and check_password_hash(usuario.senha, request.form['senha']):
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            session['nome'] = usuario.nome
            return redirect(url_for('index'))
            
        flash('Utilizador ou senha incorretos.', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ROTA DO PERFIL ATUALIZADA COM DADOS FINANCEIROS
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    usuario = Usuario.query.get(session['user_id'])
    config = Configuracao.query.filter_by(user_id=session['user_id']).first()
    
    if request.method == 'POST':
        # Atualiza Conta
        usuario.nome = request.form.get('nome')
        session['nome'] = usuario.nome
        nova_senha = request.form.get('senha')
        if nova_senha: 
            usuario.senha = generate_password_hash(nova_senha)
            
        # Atualiza Realidade Financeira
        config.meta = float(request.form.get('meta', config.meta))
        config.aporte_mensal_planejado = float(request.form.get('aporte_mensal', config.aporte_mensal_planejado))
        
        data_str = request.form.get('data_alvo')
        if data_str:
            config.data_alvo = datetime.strptime(data_str, '%Y-%m-%d').date()
            
        db.session.commit()
        flash('Perfil e metas atualizados com sucesso!', 'success')
        return redirect(url_for('perfil'))
        
    return render_template('perfil.html', user=usuario, config=config)

@app.route('/simulador', methods=['GET', 'POST'])
def simulador():
    if request.method == 'POST':
        try:
            valor = float(request.form['valor'])
            perfil = request.form['perfil']
            if perfil == 'Conservador': distribuicao = {'Renda Fixa': 0.60, 'FIIs': 0.25, 'Ações': 0.15}
            elif perfil == 'Moderado': distribuicao = {'Renda Fixa': 0.40, 'FIIs': 0.30, 'Ações': 0.30}
            elif perfil == 'Agressivo': distribuicao = {'Renda Fixa': 0.20, 'FIIs': 0.30, 'Ações': 0.50}

            valores_reais = {k: v * valor for k, v in distribuicao.items()}
            simulacao = {
                'data': datetime.now().strftime("%d/%m/%Y"),
                'valor_investido': valor,
                'perfil': perfil,
                'distribuicao_percentual': distribuicao,
                'valores_reais': valores_reais
            }
            return render_template('resultado.html', sim=simulacao)
        except ValueError:
            return redirect(url_for('simulador'))
    return render_template('simulador.html')

@app.route('/aprender')
def aprender():
    return render_template('aprender.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)