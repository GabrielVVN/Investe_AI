# Investe Aí

![Logo](https://emojicdn.elk.sh/📈)

**Investe Aí** é um sistema web premium para controle, simulação e aprendizado de investimentos, com visual moderno, dashboard interativo e trilha educacional. Ideal para quem quer sair do zero e dominar o próprio futuro financeiro.

---

## ✨ Funcionalidades Principais

- **Dashboard Dinâmico**: Visualize seu patrimônio, progresso de metas e distribuição da carteira em gráficos interativos.
- **Gestão de Investimentos**: Registre aportes reais, categorize por tipo (Ações, FIIs, Renda Fixa, Cripto) e acompanhe o histórico.
- **Simulador Inteligente**: Calcule a carteira ideal para seu perfil de risco (Conservador, Moderado, Agressivo) e veja sugestões de alocação.
- **Perfil Personalizável**: Defina meta financeira, aporte mensal, data-alvo e ajuste seus dados de conta.
- **Coach Financeiro**: Receba dicas automáticas sobre o quanto investir para atingir sua meta no prazo.
- **Trilha de Aprendizado**: Módulos educativos sobre reserva de emergência, inflação, juros compostos e tipos de ativos.
- **Visual Premium**: Interface glassmorphism, responsiva, com animações e design fintech.

---

## 🚀 Como Rodar Localmente

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repo>
   cd Investe_ai
   ```
2. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   # Se não existir, instale manualmente:
   pip install flask flask_sqlalchemy numpy_financial werkzeug
   ```
4. **Rode o sistema:**
   ```bash
   python app.py
   ```
5. **Acesse:**
   - Navegue até [http://localhost:5001](http://localhost:5001)

---

## 🗂️ Estrutura de Pastas

```
Investe_ai/
├── app.py                # Backend Flask principal
├── carteira.json         # Exemplo de aportes (mock)
├── data.json             # Exemplo de simulações (mock)
├── users.json            # Exemplo de usuários (mock)
├── instance/
│   └── investe_ai.db     # Banco de dados SQLite
├── static/
│   ├── style.css         # Estilo visual premium
│   └── animations.js     # Animações JS (opcional)
├── templates/
│   ├── base.html         # Layout base
│   ├── index.html        # Dashboard
│   ├── investir.html     # Formulário de aporte
│   ├── perfil.html       # Perfil e metas
│   ├── simulador.html    # Simulador de carteira
│   ├── resultado.html    # Resultado da simulação
│   ├── aprender.html     # Trilha de aprendizado
│   ├── cadastro.html     # Cadastro de usuário
│   └── login.html        # Login
└── venv/                 # Ambiente virtual Python
```

---

## 🧠 Tecnologias Utilizadas

- **Python 3**
- **Flask** (backend web)
- **Flask-SQLAlchemy** (ORM e banco SQLite)
- **Werkzeug** (hash de senha)
- **numpy_financial** (cálculos financeiros)
- **HTML5/CSS3** (Glassmorphism, responsivo)
- **Chart.js** (gráficos dinâmicos)

---

## 🔒 Segurança
- Senhas são armazenadas com hash seguro (Werkzeug).
- Sessões protegidas por `secret_key`.
- Autenticação obrigatória para acessar o dashboard.

---

## 📝 Como Usar

1. **Cadastro/Login:**
   - Crie uma conta ou faça login.
2. **Defina sua meta:**
   - Ajuste meta financeira, aporte mensal e data-alvo em "Perfil".
3. **Registre aportes:**
   - Clique em "+ Novo Aporte" e preencha os dados.
4. **Acompanhe o progresso:**
   - Veja gráficos, distribuição e dicas do coach financeiro.
5. **Simule carteiras:**
   - Use o simulador para ver sugestões de alocação para seu perfil.
6. **Aprenda:**
   - Explore a trilha de aprendizado para dominar conceitos essenciais.

---

## 🎨 Visual

- Glassmorphism, cores premium fintech, responsivo para mobile e desktop.
- Gráficos interativos (Chart.js) e animações suaves.

---

## 📚 Créditos & Licença

Desenvolvido por Gabriel Vieira. Sinta-se livre para usar, modificar e compartilhar!

---

## 💡 Dicas
- Para resetar o banco, apague o arquivo `instance/investe_ai.db`.
- Para customizar categorias, edite o modelo `Aporte` em `app.py`.
- Para adicionar novos módulos educativos, edite `aprender.html`.

---

## 🛠️ Roadmap Sugerido
- Exportação de relatórios PDF/Excel
- Integração com APIs de cotação
- Notificações de meta atingida
- Multiusuário avançado