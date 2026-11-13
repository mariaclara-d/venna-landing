(() => {
  'use strict';
  const phone = '5571981054103';
  const whatsappUrl = message => `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
  function trackContact(source) {
    // Counts intent to open WhatsApp, not a confirmed message or sale.
    // Never include form fields or the destination URL in event parameters.
    try {
      if (typeof window.fbq === 'function') {
        window.fbq('track', 'Contact', { contact_method: 'WhatsApp', source });
      }
    } catch (_) { /* Analytics must not prevent contact navigation. */ }
  }
  document.querySelectorAll('[data-whatsapp]').forEach(link => {
    const interest = link.dataset.whatsapp;
    const message = interest === 'oferta'
      ? 'Olá, VENNA! Tenho interesse na oferta de Travertino Rockface por R$ 136,99/m², com pedido mínimo de 50 m². Gostaria de consultar as condições e solicitar um orçamento.'
      : interest === 'geral'
      ? 'Olá, VENNA! Vim pelo site e gostaria de um orçamento.'
      : `Olá, VENNA! Vim pelo site e tenho interesse na linha ${interest}.`;
    link.href = whatsappUrl(message);
    link.addEventListener('click', () => trackContact(link.dataset.source || (interest === 'geral' ? 'link' : 'linha')));
  });

  const offer = document.getElementById('offer-dialog');
  if (offer && typeof offer.showModal === 'function') {
    const storageKey = 'venna-rockface-offer-v1';
    let previousFocus;
    const openOffer = () => {
      if (offer.open) return;
      previousFocus = document.activeElement;
      offer.showModal();
      document.body.classList.add('offer-open');
      try { sessionStorage.setItem(storageKey, 'seen'); } catch (_) {}
    };
    offer.querySelector('.offer-close').addEventListener('click', () => offer.close());
    offer.addEventListener('click', event => {
      if (event.target !== offer) return;
      const rect = offer.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) offer.close();
    });
    offer.addEventListener('close', () => {
      document.body.classList.remove('offer-open');
      if (previousFocus && previousFocus.isConnected) previousFocus.focus({ preventScroll: true });
    });
    document.querySelectorAll('[data-open-offer]').forEach(button => {
      button.hidden = false;
      button.addEventListener('click', openOffer);
    });
    let seen = false;
    try { seen = sessionStorage.getItem(storageKey) === 'seen'; } catch (_) {}
    if (!seen) openOffer();
  }

  const form = document.getElementById('quote-form');
  const name = document.getElementById('nome');
  name.addEventListener('input', () => name.setCustomValidity(''));
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!name.value.trim()) {
      name.setCustomValidity('Por favor, informe seu nome.');
      name.reportValidity();
      return;
    }
    if (!form.reportValidity()) return;
    const values = new FormData(form);
    const message = [
      values.get('interesse') === 'Travertino Rockface — oferta'
        ? 'Olá, VENNA! Tenho interesse na oferta de Travertino Rockface por R$ 136,99/m², com pedido mínimo de 50 m². Gostaria de consultar as condições e solicitar um orçamento.'
        : 'Olá, VENNA! Vim pelo site e gostaria de um orçamento.',
      `Nome: ${String(values.get('nome')).trim()}`,
      `Perfil: ${values.get('perfil')}`,
      `Interesse: ${values.get('interesse')}`,
    ];
    const area = String(values.get('metragem')).trim();
    if (area) message.push(`Metragem aproximada: ${area} m²`);
    trackContact('form');
    // Same-tab navigation avoids popup blockers in mobile and in-app browsers.
    window.location.assign(whatsappUrl(message.join('\n')));
  });

  // Hide the fixed CTA near the form and while typing so it cannot cover controls.
  const floating = document.querySelector('.floating-cta');
  const contact = document.getElementById('contato');
  let contactVisible = false;
  function updateFloating() {
    const editing = /^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName);
    floating.classList.toggle('is-hidden', contactVisible || editing);
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      contactVisible = entries[0].isIntersecting;
      updateFloating();
    }, { threshold: 0 }).observe(contact);
  }
  document.addEventListener('focusin', updateFloating);
  document.addEventListener('focusout', () => setTimeout(updateFloating, 0));
})();
