# 🥊 MMA Probability Analyzer

Sistema completo de análise de probabilidades para lutas de MMA, incluindo interface gráfica e scraper automático de dados da UFC.

## 📁 Estrutura do Projeto

```
MMA/
├── mma_prob_model.py        # Modelo de probabilidade principal
├── mma_prob_demo.py         # Demonstração do modelo
├── mma_round_demo.py        # Demo por rounds
├── mma_gui.py              # Interface gráfica
├── ufc_scraper_final.py    # Scraper UFC atualizado
├── fighter_photos/         # Pasta de fotos dos lutadores
└── README.md               # Documentação
```

## 🧠 Estatísticas Utilizadas pelo Modelo

### 📊 **Descrição das Variáveis**

**slpm**: Golpes significativos acertados por minuto
**sapm**: Golpes significativos absorvidos por minuto
**strike_acc**: Precisão dos golpes (fração)
**strike_def**: Defesa contra golpes (fração)
**td_avg15**: Quedas acertadas por 15 minutos
**td_acc**: Precisão das quedas (fração)
**td_def**: Defesa contra quedas (fração)
**sub_avg15**: Tentativas de finalização por 15 minutos
**kd_avg**: Knockdowns por 15 minutos
**aft_minutes**: Tempo médio de luta (minutos)

## 📊 Estatísticas Reais Coletadas

### Dricus Du Plessis ("Stillknocks") ✅ VERIFICADO
**Dados oficiais extraídos do site da UFC (16/08/2025):**
- **SLPM**: 6.12 (Golpes Sig. Conectados Por Minuto)
- **SAPM**: 4.90 (Golpes Sig. Absorvidos Por Minuto)
- **Strike Defense**: 54% (Defesa de Golpes Sig.)
- **TD Avg/15min**: 2.55 (Média de quedas Por 15 Min)
- **TD Defense**: 50% (Defesa De Quedas)
- **Sub Avg/15min**: 0.73 (Média de finalizações Por 15 Min)
- **KD Avg**: 0.48 (Média de Knockdowns)
- **AFT**: 13:45 (Tempo médio de luta = 13.75 min)
- **Record**: 23-2-0

## 🚀 Como Usar

### 1. Interface Gráfica
```bash
python mma_gui.py
```
- Interface completa com tema dark
- Upload de fotos dos lutadores
- Bordas escuras nas caixas de foto ✅
- Cálculo automático de probabilidades
- Resultado visual profissional

### 2. Scraper UFC
```bash
python ufc_scraper_final.py
```
- Extrai dados automaticamente do site da UFC
- Download de fotos oficiais
- Base de dados de lutadores famosos
- Fallback para estimativas por divisão

### 3. Modelo Direto
```bash
python mma_prob_demo.py
```
- Demonstração do algoritmo de probabilidade
- Exemplos práticos de cálculos

## 🔧 Recursos Técnicos

### Scraper UFC (`ufc_scraper_final.py`)
- **Múltiplas estratégias**: Requests + BeautifulSoup, com fallbacks inteligentes
- **Base de dados**: Estatísticas reais de lutadores famosos
- **Estimativas por divisão**: Quando dados específicos não disponíveis
- **Download automático**: Fotos oficiais dos lutadores
- **URLs múltiplas**: Tenta .com.br e .com automaticamente

### Interface Gráfica (`mma_gui.py`)
- **Design profissional**: Tema dark com bordas e contornos
- **Layout responsivo**: Seções organizadas e centralizadas
- **Upload de fotos**: Suporte a JPG, PNG, GIF
- **Bordas escuras**: Implementadas nas caixas de foto dos lutadores
- **Cálculo em tempo real**: Integração com modelo de probabilidade
- **Resultados visuais**: Percentuais e nomes destacados

### Modelo de Probabilidade (`mma_prob_model.py`)
- **Regressão logística**: Algoritmo matemático avançado
- **10 variáveis**: Todas as estatísticas relevantes do MMA
- **Normalização**: Tratamento adequado dos dados
- **Precisão**: Baseado em análise estatística real

## 🎯 Status do Projeto

- ✅ **Extração automática** de dados da UFC
- ✅ **Interface gráfica profissional** com tema dark
- ✅ **Bordas escuras** nas caixas de foto dos lutadores
- ✅ **Download automático** de fotos dos lutadores
- ✅ **Base de dados** com estatísticas reais verificadas
- ✅ **Modelo de probabilidade** matematicamente fundamentado
- ✅ **Múltiplas estratégias** de fallback para robustez
- ✅ **Documentação completa** com exemplos práticos

**Última atualização**: 16 de Agosto de 2025  
**Lutador verificado**: Dricus Du Plessis  
**Fonte**: UFC.com (dados oficiais coletados manualmente)