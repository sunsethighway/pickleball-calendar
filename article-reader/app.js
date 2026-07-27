(function () {
  'use strict';

  var STORAGE_KEYS = {
    text: 'reader.text',
    voiceURI: 'reader.voiceURI',
    rate: 'reader.rate'
  };

  var textArea = document.getElementById('article-text');
  var readerView = document.getElementById('reader-view');
  var btnPlay = document.getElementById('btn-play');
  var btnPause = document.getElementById('btn-pause');
  var btnStop = document.getElementById('btn-stop');
  var voiceSelect = document.getElementById('voice-select');
  var speedRange = document.getElementById('speed-range');
  var speedValueLabel = document.getElementById('speed-value');
  var statusLine = document.getElementById('status-line');

  var synth = window.speechSynthesis;
  var voices = [];
  var sentences = [];
  var currentIndex = 0;
  var stopped = true;

  // ---------- Feature detection ----------

  if (!('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') {
    statusLine.textContent = 'Speech synthesis is not supported in this browser.';
    btnPlay.disabled = true;
    return;
  }

  // ---------- Sentence chunking ----------
  // Splits on . ! ? so iOS Safari doesn't cut off long single utterances,
  // and so we can track/highlight playback progress sentence-by-sentence.
  function chunkSentences(text) {
    var normalized = text.replace(/\s+/g, ' ').trim();
    if (!normalized) return [];
    var matches = normalized.match(/[^.!?]+[.!?]+(?=\s|$)|[^.!?]+$/g);
    if (!matches) return [normalized];
    return matches.map(function (s) { return s.trim(); }).filter(Boolean);
  }

  // ---------- Reader view (highlight + auto-scroll) ----------

  function renderReaderView(list) {
    readerView.textContent = '';
    var frag = document.createDocumentFragment();
    list.forEach(function (s, i) {
      var span = document.createElement('span');
      span.className = 'sentence';
      span.dataset.index = String(i);
      span.textContent = s + ' ';
      frag.appendChild(span);
    });
    readerView.appendChild(frag);
  }

  function highlightSentence(index) {
    var prev = readerView.querySelector('.sentence.current');
    if (prev) prev.classList.remove('current');
    var el = readerView.querySelector('.sentence[data-index="' + index + '"]');
    if (el) {
      el.classList.add('current');
      el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }

  function clearHighlight() {
    var prev = readerView.querySelector('.sentence.current');
    if (prev) prev.classList.remove('current');
  }

  function showReaderView() {
    textArea.hidden = true;
    readerView.hidden = false;
  }

  function showTextEditor() {
    readerView.hidden = true;
    textArea.hidden = false;
  }

  // ---------- Button state ----------

  function setButtonsStopped() {
    btnPlay.disabled = false;
    btnPause.disabled = true;
    btnStop.disabled = true;
  }

  function setButtonsPlaying() {
    btnPlay.disabled = true;
    btnPause.disabled = false;
    btnStop.disabled = false;
  }

  function setButtonsPaused() {
    btnPlay.disabled = false;
    btnPause.disabled = true;
    btnStop.disabled = false;
  }

  // ---------- Playback ----------

  function getSelectedVoice() {
    var uri = voiceSelect.value;
    for (var i = 0; i < voices.length; i++) {
      if (voices[i].voiceURI === uri) return voices[i];
    }
    return null;
  }

  function getCurrentRate() {
    return parseFloat(speedRange.value) || 1;
  }

  function speakSentenceAt(index) {
    if (stopped) return;

    if (index >= sentences.length) {
      finishPlayback();
      return;
    }

    currentIndex = index;
    var utterance = new SpeechSynthesisUtterance(sentences[index]);
    var voice = getSelectedVoice();
    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang;
    } else {
      utterance.lang = 'en-US';
    }
    utterance.rate = getCurrentRate();

    utterance.onend = function () {
      if (stopped) return;
      speakSentenceAt(index + 1);
    };

    utterance.onerror = function (event) {
      if (stopped) return;
      // 'interrupted' / 'canceled' happen when we intentionally cancel; anything
      // else (e.g. a bad voice) shouldn't stall the whole article, so skip ahead.
      if (event.error === 'interrupted' || event.error === 'canceled') return;
      speakSentenceAt(index + 1);
    };

    highlightSentence(index);
    statusLine.textContent = 'Sentence ' + (index + 1) + ' of ' + sentences.length;
    synth.speak(utterance);
  }

  function finishPlayback() {
    stopped = true;
    clearHighlight();
    showTextEditor();
    setButtonsStopped();
    statusLine.textContent = '';
  }

  function startPlayback() {
    var text = textArea.value.trim();
    if (!text) return;

    sentences = chunkSentences(text);
    if (sentences.length === 0) return;

    renderReaderView(sentences);
    showReaderView();
    stopped = false;
    setButtonsPlaying();
    speakSentenceAt(0);
  }

  // iOS requires the very first speak() call to happen synchronously inside
  // a direct tap handler — no async work before it.
  btnPlay.addEventListener('click', function () {
    if (synth.paused && synth.speaking) {
      synth.resume();
      setButtonsPlaying();
      return;
    }
    if (!stopped && synth.speaking) return;
    startPlayback();
  });

  btnPause.addEventListener('click', function () {
    if (synth.speaking && !synth.paused) {
      synth.pause();
      setButtonsPaused();
    }
  });

  btnStop.addEventListener('click', function () {
    stopped = true;
    synth.cancel();
    clearHighlight();
    showTextEditor();
    setButtonsStopped();
    statusLine.textContent = '';
  });

  // ---------- Voice list ----------
  // getVoices() loads asynchronously on iOS — the list is only reliable
  // once 'voiceschanged' has fired at least once.

  function populateVoiceList() {
    var all = synth.getVoices();
    voices = all.filter(function (v) {
      return v.lang && v.lang.toLowerCase().indexOf('en') === 0;
    });

    var wanted = voiceSelect.value || localStorage.getItem(STORAGE_KEYS.voiceURI);

    voiceSelect.innerHTML = '';

    if (voices.length === 0) {
      var placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.textContent = 'Loading voices…';
      voiceSelect.appendChild(placeholder);
      return;
    }

    voices.forEach(function (v) {
      var opt = document.createElement('option');
      opt.value = v.voiceURI;
      opt.textContent = v.name + ' (' + v.lang + ')' + (v.default ? ' — default' : '');
      voiceSelect.appendChild(opt);
    });

    if (wanted && voices.some(function (v) { return v.voiceURI === wanted; })) {
      voiceSelect.value = wanted;
    }
  }

  synth.addEventListener('voiceschanged', populateVoiceList);
  populateVoiceList();
  // Fallback for browsers/webviews that never fire voiceschanged.
  setTimeout(populateVoiceList, 500);
  setTimeout(populateVoiceList, 1500);

  voiceSelect.addEventListener('change', function () {
    localStorage.setItem(STORAGE_KEYS.voiceURI, voiceSelect.value);
  });

  // ---------- Speed ----------

  function formatRate(val) {
    return (Math.round(val * 100) / 100) + 'x';
  }

  function updateSpeedLabel() {
    speedValueLabel.textContent = formatRate(getCurrentRate());
  }

  speedRange.addEventListener('input', function () {
    updateSpeedLabel();
    localStorage.setItem(STORAGE_KEYS.rate, speedRange.value);
  });

  // ---------- Persistence ----------

  var saveTextTimer = null;
  textArea.addEventListener('input', function () {
    clearTimeout(saveTextTimer);
    saveTextTimer = setTimeout(function () {
      localStorage.setItem(STORAGE_KEYS.text, textArea.value);
    }, 300);
  });

  function loadState() {
    var savedText = localStorage.getItem(STORAGE_KEYS.text);
    if (savedText) textArea.value = savedText;

    var savedRate = parseFloat(localStorage.getItem(STORAGE_KEYS.rate));
    if (!isNaN(savedRate) && savedRate >= 0.5 && savedRate <= 2) {
      speedRange.value = String(savedRate);
    }
    updateSpeedLabel();
  }

  loadState();
  setButtonsStopped();

  // ---------- Service worker ----------

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('service-worker.js').catch(function () {});
    });
  }
})();
