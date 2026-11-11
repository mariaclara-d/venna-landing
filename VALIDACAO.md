# Landing page VENNA

Site estático publicado a partir de `site/`, sem instalação de dependências nem etapa de build. Mantido o fluxo GitHub → Vercel.

## Desenvolvimento

Execute `python -m http.server 8765 --bind 127.0.0.1 --directory site` e abra `http://127.0.0.1:8765`.

- `site/index.html`: conteúdo e links de contato disponíveis mesmo sem JavaScript.
- `site/styles.css`: layout responsivo e fontes locais.
- `site/app.js`: mensagem de orçamento e comportamento do botão fixo.
- `site/img/pedra-moledo-champagne.webp`: foto fornecida para Pedras naturais.

## Verificação em 10/11/2026

Com Python, Playwright e Chrome instalados, execute `python scripts/check_landing.py` enquanto o servidor local estiver ativo. O teste intercepta a navegação ao WhatsApp; nenhuma mensagem é enviada. Relatório e capturas ficam em `TEMP/venna-qa`.

Verificado em Chrome nas larguras de 320, 375, 390, 430, 768, 1024, 1440 e 1920 pixels: sem rolagem horizontal, recursos HTTP com erro ou exceções JavaScript. Verificados imagens, validação do nome, mensagem com metragem decimal e conteúdo sem JavaScript. Isso não substitui testes em aparelhos reais, Safari e navegador interno do aplicativo Meta.

## Pendências antes dos anúncios

- WhatsApp `5571981054103` confirmado pela responsável. Ao alterar o número, atualizar tanto `index.html` quanto `app.js`.
- Atendimento em todo o Brasil e CNPJ `69.965.547/0001-28` informados pela responsável e incluídos na página. Prazos e condições de entrega são consultados no atendimento.
- Meta Pixel `2114568142517377` instalado: `PageView` na abertura da página e `Contact` ao clicar em um link de WhatsApp ou continuar pelo formulário válido. `Contact` mede intenção de contato, não mensagem enviada ou venda. Os parâmetros enviados pelo código são apenas canal (`WhatsApp`) e origem (`link` ou `form`), sem campos do formulário. Não foi configurada API de Conversões.
- Confirmar o recebimento em “Testar eventos” no Gerenciador de Eventos após o deploy. Bloqueadores de anúncios podem impedir a medição.
- Acompanhar o deploy na Vercel e fazer um contato de teste no celular com o número confirmado.
