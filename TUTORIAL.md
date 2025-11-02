# Tutorial - Auto Preenchedor de Formulários

## Índice
1. [Introdução](#introdução)
2. [Requisitos](#requisitos)
3. [Instalação](#instalação)
4. [Configuração Inicial](#configuração-inicial)
5. [Como Usar](#como-usar)
6. [Funcionalidades Avançadas](#funcionalidades-avançadas)
7. [Solução de Problemas](#solução-de-problemas)

---

## Introdução

O **Auto Preenchedor** é uma ferramenta automatizada que facilita o preenchimento de formulários CIPTEA e Intermunicipal. O sistema utiliza Inteligência Artificial (Google Gemini) para extrair dados de documentos digitalizados e preenche automaticamente os formulários web.

### Principais Funcionalidades
- ✅ Coleta de documentos via drag-and-drop
- ✅ Extração automática de dados com IA
- ✅ Validação e edição manual de dados
- ✅ Preenchimento automático de 3 formulários diferentes
- ✅ Suporte para documento VEM (Vale Eletrônico Municipal)
- ✅ Organização automática de arquivos
- ✅ Conversão automática de imagens para PDF

---

## Requisitos

### Software Necessário
- **Python 3.11 ou superior**
- **Google Chrome** (para automação web)
- **Conexão com internet** (para IA e acesso aos formulários)

### Documentos Necessários
- 📄 **CPF do Beneficiário** (obrigatório)
- 📄 RG do Beneficiário (opcional)
- 📷 **Foto 3x4** (obrigatório)
- 📄 **CPF do Responsável** (obrigatório)
- 📄 RG do Responsável (opcional)
- 📄 **Laudo Médico** (obrigatório)
- 📄 **Comprovante de Residência** (obrigatório)
- 📄 VEM - Vale Eletrônico Municipal (opcional)

> **Nota:** Os itens em negrito são obrigatórios.

---

## Instalação

### 1. Instalar Dependências

Abra o terminal no diretório do projeto e execute:

```bash
pip install -r requirements.txt
```

Ou instale manualmente:

```bash
pip install PyQt5 pillow img2pdf python-dotenv google-generativeai selenium unidecode
```

### 2. Instalar ChromeDriver

O ChromeDriver é necessário para automação web. Certifique-se de ter o Google Chrome instalado e o ChromeDriver compatível com sua versão do Chrome.

### 3. Obter API Key do Google

1. Acesse [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Crie uma nova API Key
3. Copie a chave gerada

### 4. Gerar Executável (Opcional)

Se você deseja criar um arquivo executável (.exe) para distribuir o programa:

```bash
pip install pyinstaller
```

Em seguida, execute o arquivo batch:

```bash
pyinstaller_command.bat
```

Ou execute diretamente o comando PyInstaller:

```bash
pyinstaller --onefile --windowed ui.py
```

O executável será gerado em `dist/ui.exe`

**Parâmetros utilizados:**
- `--onefile`: Gera um único arquivo executável
- `--windowed`: Remove a janela do console (interface apenas gráfica)
- `ui.py`: Arquivo principal do programa

> **💡 Dica:** O processo pode levar alguns minutos. O executável gerado pode ser distribuído sem necessidade de instalar Python!

---

## Configuração Inicial

### Configurar API Key

A API Key do Google é necessária para extração de dados com IA.

**Método 1: Via Interface (Recomendado)**
1. Execute o programa: `python ui.py`
2. **Clique com botão direito** no banner azul escuro (topo da janela)
3. Selecione "🔑 Configurar API Key"
4. Cole sua API Key do Google
5. Clique em OK

**Método 2: Manualmente**
1. Crie o arquivo `.env` em `C:\Users\SEU_USUARIO\.auto_preenchedor_data\.env`
2. Adicione a linha:
   ```
   GOOGLE_API_KEY=sua_chave_aqui
   ```

---

## Como Usar

### Passo 1: Coleta de Documentos

![Tela de Coleta de Documentos - ADICIONAR SCREENSHOT AQUI]

1. **Inicie o programa:**
   ```bash
   python ui.py
   ```

2. **Digite o nome do beneficiário** no campo superior

3. **Adicione os documentos:**
   - **Arraste e solte** as imagens nas áreas indicadas, ou
   - **Clique** na área para selecionar o arquivo

4. **Documentos obrigatórios** estão marcados com **asterisco vermelho (*)**

5. **Acompanhe o progresso:**
   - O contador mostra quantos documentos foram carregados
   - Exemplo: "5/8 documentos carregados (VEM opcional)"

6. **Clique em "Próximo: Extração de Dados ➜"**

> **💡 Dica:** Você pode arrastar imagens entre as áreas para reorganizar!

---

### Passo 2: Verificação e Edição de Dados

![Tela de Edição de Dados - ADICIONAR SCREENSHOT AQUI]

#### Extração Automática
O sistema irá:
1. ✅ Organizar os documentos em uma pasta
2. ✅ Criar colagem das imagens
3. ✅ Extrair texto com IA (Google Gemini)
4. ✅ Processar e estruturar os dados

#### Revisar Dados Extraídos

![Campos de Dados - ADICIONAR SCREENSHOT AQUI]

**Dados do Responsável:**
- Nome do Responsável (automático MAIÚSCULAS)
- CPF do Responsável (formato: 000.000.000-00)
- RG do Responsável

**Dados do Beneficiário:**
- Nome do Beneficiário (automático MAIÚSCULAS)
- Nome da Mãe do Beneficiário (automático MAIÚSCULAS)
- CPF do Beneficiário (formato: 000.000.000-00)
- RG do Beneficiário
- Data de Nascimento (DD/MM/AAAA)

**Dados de Contato:**
- Endereço (Rua e Número)
- CEP (formato: 00000-000)
- Telefone (formato: (81) 9 9999-9999)
- E-mail

> **💡 Dica:** Os campos formatam automaticamente enquanto você digita!

---

### Passo 3: Selecionar CIDs

![Seleção de CIDs - ADICIONAR SCREENSHOT AQUI]

1. **Role até a seção "CIDs - Selecione todos os aplicáveis"**
2. **Marque todos os CIDs aplicáveis:**
   - Coluna esquerda: CID-10 (F84.0 a F84.9)
   - Coluna direita: CID-11 (6A02.0 a 6A02.Z)

> **⚠️ Atenção:** A IA tenta marcar automaticamente, mas sempre revise!

---

### Passo 4: Selecionar Formulários

![Seleção de Formulários - ADICIONAR SCREENSHOT AQUI]

Escolha quais formulários deseja preencher:

**CIPTEA Primeira Via**
- ☑️ Marcado por padrão
- Para primeira solicitação da carteirinha

**CIPTEA Segunda Via**
- ☐ Desmarcado por padrão
- Para renovação/segunda via
- **Exclusivo:** Não pode marcar junto com Primeira Via

**Intermunicipal**
- ☑️ Marcado por padrão
- Para passe intermunicipal
- **↳ Usar Documento VEM:** Marque se tiver o documento VEM

> **⚠️ Importante:** Role até o final da página para habilitar o botão "Próximo"

---

### Passo 5: Preenchimento Automático

![Botão Preencher Formulários - ADICIONAR SCREENSHOT AQUI]

1. **Clique em "Próximo: Preencher Formulários ➜"**

2. **O sistema irá:**
   - ✅ Abrir o navegador Chrome
   - ✅ Preencher Formulário Intermunicipal (se selecionado)
   - ✅ Preencher CIPTEA Primeira ou Segunda Via
   - ✅ Anexar todos os documentos automaticamente

3. **Aguarde a mensagem de conclusão**

![Navegador com Formulários - ADICIONAR SCREENSHOT AQUI]

4. **Revise os dados preenchidos** em cada aba do navegador

5. **Submeta os formulários manualmente** após confirmar

> **💡 Dica:** O Intermunicipal é preenchido primeiro, então as abas CIPTEA ficam em destaque!

---

## Funcionalidades Avançadas

### 🔄 Nova Entrada

![Botão Nova Entrada - ADICIONAR SCREENSHOT AQUI]

Permite começar um novo preenchimento sem fechar o programa:

1. Clique em "🔄 Nova Entrada"
2. Confirme na mensagem de aviso
3. Todos os dados serão limpos
4. Você retorna à tela inicial

> **⚠️ Atenção:** Esta ação não pode ser desfeita!

---

### 📁 Abrir Pasta

![Botão Abrir Pasta - ADICIONAR SCREENSHOT AQUI]

Acessa rapidamente os arquivos organizados:

1. Clique em "📁 Abrir Pasta"
2. O Windows Explorer abre na pasta com:
   - ✅ Todos os documentos organizados
   - ✅ PDFs convertidos
   - ✅ Colagem gerada para IA
   - ✅ Dados extraídos em JSON

**Localização:** `C:\Users\SEU_USUARIO\.auto_preenchedor_data\nome_do_beneficiario\`

---

### 🧪 Dados de Teste

![Menu de Dados de Teste - ADICIONAR SCREENSHOT AQUI]

Para desenvolvedores e testes:

1. **Clique com botão direito** no botão "Próximo" da primeira tela
2. Selecione "🧪 Carregar Dados de Teste"
3. Dados de exemplo serão carregados automaticamente

> **Nota:** Requer arquivo `data_example.json` no diretório

---

### ⚙️ Configurações Avançadas

#### Alterar API Key
1. Clique com botão direito no banner azul (topo)
2. Selecione "🔑 Configurar API Key"
3. Digite a nova chave
4. A chave é salva automaticamente

#### Localização da Configuração
```
C:\Users\SEU_USUARIO\.auto_preenchedor_data\.env
```

---

## Solução de Problemas

### ❌ Erro: "API Key not found"

**Problema:** API Key não configurada

**Solução:**
1. Clique com botão direito no banner azul
2. Selecione "🔑 Configurar API Key"
3. Cole sua chave do Google
4. Reinicie o programa

---

### ❌ Erro ao extrair dados

**Problema:** IA não conseguiu extrair dados corretamente

**Solução:**
1. Verifique a qualidade das imagens (resolução mínima 300 DPI)
2. Certifique-se que o texto está legível
3. Edite manualmente os campos incorretos
4. Exclua a foto 3x4 e VEM da colagem (já implementado)

---

### ❌ ChromeDriver não encontrado

**Problema:** Selenium não consegue abrir o Chrome

**Solução:**
1. Verifique se o Chrome está instalado
2. Baixe ChromeDriver compatível: [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads)
3. Adicione ao PATH do sistema

---

### ❌ Documentos não anexados

**Problema:** Arquivos não foram anexados ao formulário

**Solução:**
1. Verifique se os documentos estão na pasta organizada
2. Confirme que os PDFs foram gerados
3. Para VEM: Certifique-se que marcou "Usar Documento VEM"
4. Recarregue a página e tente novamente

---

### ❌ Botão "Próximo" desabilitado

**Problema:** Não consigo clicar em "Próximo: Preencher Formulários"

**Solução:**
1. **Role até o final da página** (requisito de segurança)
2. Certifique-se que **pelo menos um formulário** está marcado
3. O botão ficará verde quando habilitado

---

### ❌ Formatação de campos não funciona

**Problema:** CPF, telefone, etc. não formatam automaticamente

**Solução:**
1. Digite apenas números
2. A formatação acontece automaticamente ao digitar
3. Para nomes: Letras minúsculas são convertidas para MAIÚSCULAS

---

### 💾 Backup de Dados

Seus dados são salvos automaticamente em:
```
C:\Users\SEU_USUARIO\.auto_preenchedor_data\
```

Cada beneficiário tem sua própria pasta com:
- 📁 Documentos originais
- 📁 PDFs convertidos
- 📄 Dados extraídos (JSON)
- 🖼️ Colagem gerada

---

## Dicas e Boas Práticas

### 📸 Qualidade das Imagens
- ✅ Use resolução mínima de 300 DPI
- ✅ Certifique-se que o texto está legível
- ✅ Evite sombras e reflexos
- ✅ Mantenha o documento reto (sem inclinação)

### 📝 Revisão de Dados
- ✅ **Sempre revise** os dados extraídos antes de continuar
- ✅ Preste atenção especial em CPF e datas
- ✅ Verifique se todos os CIDs estão corretos
- ✅ Confirme o endereço completo

### 🔒 Segurança
- ✅ Não compartilhe sua API Key
- ✅ Mantenha backups dos documentos originais
- ✅ Revise os formulários antes de submeter

### ⚡ Performance
- ✅ Mantenha o programa atualizado
- ✅ Use imagens em formato JPG ou PNG
- ✅ Evite documentos muito grandes (> 5MB)

---

## Atalhos de Teclado

| Ação | Atalho |
|------|--------|
| Voltar | Botão "← Voltar" |
| Nova Entrada | Botão "🔄 Nova Entrada" |
| Abrir Pasta | Botão "📁 Abrir Pasta" |
| Configurar API | Botão direito no banner |
| Dados de Teste | Botão direito em "Próximo" |

---

## Suporte

Para problemas técnicos ou dúvidas:
1. Verifique a seção [Solução de Problemas](#solução-de-problemas)
2. Revise os logs do console
3. Entre em contato com o suporte técnico

---

## Changelog

### Versão 1.0 (Novembro 2025)
- ✨ Lançamento inicial
- ✅ Suporte para CIPTEA e Intermunicipal
- ✅ Extração de dados com IA
- ✅ Automação web completa
- ✅ Suporte para documento VEM
- ✅ Interface intuitiva com drag-and-drop
- ✅ Formatação automática de campos
- ✅ Organização automática de arquivos

---

**Desenvolvido com ❤️ para facilitar o processo de obtenção de benefícios**
