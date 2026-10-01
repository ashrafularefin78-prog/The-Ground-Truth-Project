/* Ground Truth Project — optional enhancements.
 *
 * The site is complete without this file. Every sentence, number, chart,
 * table and link on every page is in the HTML that the build wrote, which is
 * what makes the "works with no JavaScript" change request a non-event.
 *
 * Rules this file follows, and tools/check.py enforces:
 *   - it never creates or rewrites page text (no innerHTML, no textContent
 *     assignment, no document.write);
 *   - it only reacts to the user: copy a prepared message, open the print
 *     dialog, hand a filled-in form to the visitor's own email app.
 */
(function () {
  'use strict';

  function copyText(text, onDone, onFail) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(onDone, onFail);
      return;
    }
    try {
      var helper = document.createElement('textarea');
      helper.value = text;
      helper.setAttribute('aria-hidden', 'true');
      helper.style.position = 'fixed';
      helper.style.top = '-1000px';
      document.body.appendChild(helper);
      helper.select();
      var copied = document.execCommand('copy');
      document.body.removeChild(helper);
      if (copied) { onDone(); } else { onFail(); }
    } catch (error) {
      onFail();
    }
  }

  function setupCopyButtons() {
    var buttons = document.querySelectorAll('[data-copy-target]');
    Array.prototype.forEach.call(buttons, function (button) {
      button.addEventListener('click', function () {
        var source = document.getElementById(button.getAttribute('data-copy-target'));
        if (!source) { return; }
        var text = source.textContent || '';
        copyText(text, function () {
          button.classList.add('is-copied');
          window.setTimeout(function () { button.classList.remove('is-copied'); }, 4000);
        }, function () {
          button.classList.add('is-copy-failed');
        });
      });
    });
  }

  function setupPrintButtons() {
    var buttons = document.querySelectorAll('[data-print]');
    Array.prototype.forEach.call(buttons, function (button) {
      button.addEventListener('click', function () {
        window.print();
      });
    });
  }

  function setupFormHandoff() {
    var form = document.querySelector('[data-mailto-form]');
    if (!form) { return; }
    form.addEventListener('submit', function (event) {
      var address = form.getAttribute('data-mailto-form');
      var subject = form.getAttribute('data-subject') || '';
      var lines = [];
      Array.prototype.forEach.call(form.elements, function (field) {
        if (!field.name || field.type === 'submit') { return; }
        var label = field.getAttribute('data-label') || field.name;
        var value = (field.value || '').trim();
        if (value) { lines.push(label + ': ' + value); }
      });
      lines.push('');
      lines.push('Sent from the Ground Truth page: ' + window.location.href);
      var href = 'mailto:' + address
        + '?subject=' + encodeURIComponent(subject)
        + '&body=' + encodeURIComponent(lines.join('\n'));
      event.preventDefault();
      window.location.href = href;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    setupCopyButtons();
    setupPrintButtons();
    setupFormHandoff();
  }
})();
