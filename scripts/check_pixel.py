"""Verify Pixel calls locally without sending events to Meta or WhatsApp."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1] / 'site'
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context()
        # Empty script keeps the official bootstrap queue inspectable.
        context.route('https://connect.facebook.net/**', lambda r: r.fulfill(status=200, content_type='text/javascript', body=''))
        context.route('https://www.facebook.com/**', lambda r: r.abort())
        context.route('https://wa.me/**', lambda r: r.abort())
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(url, wait_until='networkidle')
        page.locator('.offer-close').click()
        queue = lambda: page.evaluate('fbq.queue.map(args => Array.from(args))')
        assert queue() == [['init', '2114568142517377'], ['track', 'PageView']]
        page.evaluate("document.querySelector('.header-cta').addEventListener('click', e => e.preventDefault())")
        page.locator('.header-cta').click()
        assert queue()[-1] == ['track', 'Contact', {'contact_method': 'WhatsApp', 'source': 'link'}]
        page.locator('#nome').fill('   ')
        page.locator('button[type=submit]').click()
        assert len(queue()) == 3, 'Invalid form must not track a contact'
        page.locator('#nome').fill('Private test name')
        page.locator('#metragem').fill('25,5')
        events = queue()
        page.expose_function('capturePixelCall', lambda args: events.append(args))
        page.evaluate('''() => {
          const original = window.fbq;
          window.fbq = (...args) => { window.capturePixelCall(args); original(...args); };
        }''')
        page.locator('button[type=submit]').click()
        page.wait_for_timeout(250)
        assert events[-1] == ['track', 'Contact', {'contact_method': 'WhatsApp', 'source': 'form'}]
        assert len(events) == 4
        assert 'Private test name' not in str(events) and '25,5' not in str(events)
        page.goto(url, wait_until='networkidle')
        page.evaluate("window.fbq = () => { throw Error('blocked analytics'); }; document.querySelector('.header-cta').addEventListener('click', e => e.preventDefault())")
        page.locator('.header-cta').click()
        assert not errors, errors
        browser.close()
        print('PASS: pixel ID, single PageView, link Contact, valid-form Contact, invalid-form exclusion, no form data in parameters, and analytics failure isolation.')
finally:
    server.shutdown()
    server.server_close()
