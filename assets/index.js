const params = new URLSearchParams(window.location.search);

let reloadUponGettingOnline = false;

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

window.addEventListener("online", function () {
  if (reloadUponGettingOnline) {
    window.location.reload();
  }
});

function toggleParam(param) {
  if (params.has(param)) {
    params.delete(param);
  } else {
    params.append(param, "");
  }

  window.location.search = "?" + params.toString();
}

if (params.has("scroll")) {
  pageScroll(false);
}

if (params.has("refresh")) {
  setTimeout(function () {
    if (navigator.onLine) {
      window.location.reload();
    } else {
      reloadUponGettingOnline = true;
    }
  }, 5 * 1000);
}

if (!params.has("no-menu")) {
  const menu = document.createElement("div");
  menu.classList.add("menu");

  const buttons = [
    { param: "scroll", label: "↕️", title: "Toggle scroll" },
    { param: "refresh", label: "🔄", title: "Toggle refresh" },
    { param: "no-menu", label: "🚫", title: "Hide menu" },
  ];

  buttons.forEach(function ({ id, param, label, title }) {
    const button = document.createElement("button");
    button.innerText = label;
    button.title = title;
    button.addEventListener("click", function () {
      toggleParam(param);
    });
    menu.appendChild(button);
  });

  document.body.appendChild(menu);
}
