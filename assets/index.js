function pageScroll(jumpToTop) {
  let wait = false;

  if (jumpToTop) {
    window.scrollTo(0, 0);
  } else {
    window.scrollBy(0, 1);

    wait =
      Math.abs(
        window.innerHeight +
          window.scrollY -
          document.documentElement.offsetHeight,
      ) < 1;
  }

  if (wait) {
    setTimeout(function () {
      pageScroll(true);
    }, 5000);
  } else {
    setTimeout(function () {
      pageScroll(false);
    }, 30);
  }
}

if (document.location.search === "?scroll") {
  pageScroll(false);
}
