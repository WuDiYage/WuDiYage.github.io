// 引擎仍从 CDN 加载（1.0.1）；文案与模型走本地，便于自定义
const live2d_path = "https://fastly.jsdelivr.net/npm/live2d-widgets@1.0.1/dist/";
const local_base = "./live2d-waifu/";

// 封装异步加载资源的方法
function loadExternalResource(url, type) {
	return new Promise((resolve, reject) => {
		let tag;

		if (type === "css") {
			tag = document.createElement("link");
			tag.rel = "stylesheet";
			tag.href = url;
		}
		else if (type === "js") {
			tag = document.createElement("script");
			tag.type = "module";
			tag.src = url;
		}
		if (tag) {
			tag.onload = () => resolve(url);
			tag.onerror = () => reject(url);
			document.head.appendChild(tag);
		}
	});
}

// 避免图片资源跨域导致 WebGL 贴图失败（本地同源也可保留）
const OriginalImage = window.Image;
window.Image = function (...args) {
	const img = new OriginalImage(...args);
	img.crossOrigin = "anonymous";
	return img;
};
window.Image.prototype = OriginalImage.prototype;

// 仅在桌面宽度下加载看板娘
if (screen.width >= 768) {
	Promise.all([
		loadExternalResource(local_base + "waifu.css", "css"),
		loadExternalResource(live2d_path + "waifu-tips.js", "js")
	]).then(() => {
		initWidget({
			waifuPath: local_base + "waifu-tips.json",
			cdnPath: local_base + "live2d_api/",
			cubism2Path: live2d_path + "live2d.min.js",
			cubism5Path: "https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js",
			tools: ["hitokoto", "asteroids", "switch-model", "switch-texture", "photo", "info", "quit"],
			logLevel: "warn"
		});
	});
}

console.log(`
  く__,.ヘヽ.        /  ,ー､ 〉
           ＼ ', !-─‐-i  /  /´
           ／｀ｰ'       L/／｀ヽ､
         /   ／,   /|   ,   ,       ',
       ｲ   / /-‐/  ｉ  L_ ﾊ ヽ!   i
        ﾚ ﾍ 7ｲ｀ﾄ   ﾚ'ｧ-ﾄ､!ハ|   |
          !,/7 '0'     ´0iソ|    |
          |.从"    _     ,,,, / |./    |
          ﾚ'| i＞.､,,__  _,.イ /   .i   |
            ﾚ'| | / k_７_/ﾚ'ヽ,  ﾊ.  |
              | |/i 〈|/   i  ,.ﾍ |  i  |
             .|/ /  ｉ：    ﾍ!    ＼  |
              kヽ>､ﾊ    _,.ﾍ､    /､!
              !'〈//｀Ｔ´', ＼ ｀'7'ｰr'
              ﾚ'ヽL__|___i,___,ンﾚ|ノ
                  ﾄ-,/  |___./
                  'ｰ'    !_,.:
`);
