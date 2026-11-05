// 상단 바 색, 등장, 폰 메뉴, 예약 문자, 사진 크게 보기 — 라이브러리 없음
(function () {
  var top = document.querySelector('.top'), hero = document.querySelector('.hero');
  if (top) {
    if (!hero) top.classList.add('solid');
    else new IntersectionObserver(function (e) { top.classList.toggle('solid', !e[0].isIntersecting); }, { rootMargin: '-76px 0px 0px 0px' }).observe(hero);
  }
  var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { threshold: .12 });
  document.querySelectorAll('.rv').forEach(function (el) { io.observe(el); });

  var sheet = document.querySelector('.sheet');
  document.querySelectorAll('[data-menu]').forEach(function (b) {
    b.addEventListener('click', function () { if (sheet.open) sheet.close(); else sheet.show(); document.body.style.overflow = sheet.open ? 'hidden' : ''; });
  });

  // 예약 띠: 날짜·박·인원 → 문자 한 통
  document.querySelectorAll('form.ask').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var d = f.date.value, n = f.nights.value, p = f.people.value, name = f.dataset.name, tel = f.dataset.sms;
      var when = d ? d.replace(/-/g, '.').slice(2) + ' 입실' : '날짜 미정';
      var body = name + ' 예약 문의드립니다. ' + when + ', ' + n + '박, ' + p + '명. 빈 날짜와 요금 알려 주세요.';
      location.href = 'sms:' + tel + '?&body=' + encodeURIComponent(body);
    });
  });

  var lb = document.querySelector('dialog.lb');
  if (lb) {
    var img = lb.querySelector('img');
    document.querySelectorAll('[data-full]').forEach(function (b) {
      b.addEventListener('click', function () { img.src = b.dataset.full; img.alt = b.querySelector('img').alt; lb.showModal(); });
    });
    lb.addEventListener('click', function (e) { if (e.target === lb || e.target.tagName === 'BUTTON') lb.close(); });
  }
})();
