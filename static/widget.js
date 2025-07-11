  document.getElementById("toggle-size").addEventListener("click", () => {
    parent.postMessage({ type: "toggle-expand" }, "*");
  });

function fixLinks(text) {
  return text.replace(/<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)<\/a>/gi, (match, href, label) => {
    let target = "_blank";
    if (href.includes("tcba.com.ar")) {
      href = href.replace("https://www.tcba.com.ar", "http://www.tcba.com.ar");
      target = "_parent";
    } else if (href.includes("widget.html")) {
      target = "_self";
    }
    return `<a href="${href}" target="${target}">${label}</a>`;
  });
}
