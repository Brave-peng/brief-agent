/* Marp 模板 - 渐变风格 */
<style>
.row { display: flex; gap: 30px; align-items: center; }
.col-img { flex: 0 0 45%; }
.col-text { flex: 1; }
.cover {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}
.cover h1 { color: #ffffff !important; font-size: 2.5em; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.cover p { color: rgba(255,255,255,0.95); font-size: 1.2em; }
.ending {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  height: 100%;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}
.ending h1 { color: #fff !important; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }
section { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }
h1 { color: #7c3aed; font-size: 1.8em; font-weight: 700; background: linear-gradient(90deg, #ede9fe 0%, transparent 100%); padding: 12px 20px; border-radius: 8px; }
h2 { color: #6d28d9; font-size: 1.4em; font-weight: 600; }
ul li { margin: 10px 0; line-height: 1.8; color: #4b5563; position: relative; padding-left: 25px; }
ul li::before { content: "◆"; position: absolute; left: 0; color: #a78bfa; font-size: 0.8em; }
img { border-radius: 12px; box-shadow: 0 8px 25px rgba(124, 58, 237, 0.25); transform: translateZ(0); }
section { background: linear-gradient(180deg, #faf5ff 0%, #ffffff 100%); }
</style>
