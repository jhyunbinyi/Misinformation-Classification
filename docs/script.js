/**
 * Factuality Evaluator — GitHub Pages
 * Update the config below for your deployment, then the page will use it.
 */
(function () {
  var config = {
    streamlitAppUrl: 'https://misinformation-classification.streamlit.app/',
    reportUrl: '',   // e.g. 'https://your-site.com/report.pdf' or ''
    githubUrl: 'https://github.com/jhyunbinyi/Misinformation-Classification'
  };

  function applyConfig() {
    var demoLinks = document.querySelectorAll('.js-demo-link');
    demoLinks.forEach(function (el) {
      if (el && el.href) el.href = config.streamlitAppUrl;
    });

    var reportLink = document.getElementById('report-link');
    var reportItem = document.getElementById('report-item');
    if (reportLink && reportItem) {
      if (config.reportUrl) {
        reportLink.href = config.reportUrl;
      } else {
        reportItem.classList.add('hidden');
      }
    }

    var githubLink = document.getElementById('github-link');
    var githubItem = document.getElementById('github-item');
    if (githubLink && githubItem) {
      if (config.githubUrl) {
        githubLink.href = config.githubUrl;
      } else {
        githubItem.classList.add('hidden');
      }
    }
  }

  function initExpander() {
    var trigger = document.getElementById('prompting-trigger');
    var content = document.getElementById('prompting-content');
    var wrapper = document.getElementById('prompting-expander');
    if (!trigger || !content || !wrapper) return;

    trigger.addEventListener('click', function () {
      var isOpen = content.hidden;
      content.hidden = !isOpen;
      trigger.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
      wrapper.setAttribute('data-open', isOpen ? 'true' : '');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      applyConfig();
      initExpander();
    });
  } else {
    applyConfig();
    initExpander();
  }
})();
