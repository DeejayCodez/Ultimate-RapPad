import sys, json, re, math, random, urllib.request, urllib.error, tempfile, zipfile, subprocess, shutil
from PySide6.QtCore import Signal, QThread
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPen
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QFrame, QSplitter, QComboBox, QSpinBox, QSlider,
    QFileDialog, QMessageBox, QProgressBar, QGraphicsOpacityEffect,
    QScrollArea, QCheckBox
)

APP_NAME = "The Ultimate RapPad"
APP_VERSION = "2.0.0"
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
UPDATE_CONFIG = APP_DIR / "update_config.json"
DATA_DIR = Path.home() / "Documents" / "UltimateRapPad"
DATA_DIR.mkdir(parents=True, exist_ok=True)
AUTOSAVE = DATA_DIR / "autosave.json"

# A compact built-in rhyme seed bank keeps the app useful without internet.
# Install pronouncing for a much larger phonetic rhyme database.
SEED_WORDS = """
flow glow show know grow slow throw though below overflow
fire higher desire wire choir liar inspire entire empire
pain rain chain brain stain remain explain insane refrain
mind time rhyme climb shine design divine align combine
cold told bold gold hold unfold control soul whole role
night light fight right write sight tight ignite midnight
dream scheme team beam stream cream supreme extreme
heart start part art chart smart depart restart
game name flame claim frame aim became
real feel steel heal reveal conceal appeal ideal
pressure measure treasure pleasure weather together forever
motion ocean devotion explosion commotion potion
elevate generate separate celebrate meditate demonstrate
rational national tactical radical mechanical lyrical miracle
danger stranger anger chamber remember December surrender
broken spoken token open hoping coping focus lotus notice
victory history mystery misery energy synergy legacy
battle cattle rattled travel gravel unravel channel panel
ghost coast most post boast close chose froze
king ring bring swing thing spring sting
word heard blurred absurd disturbed deserved preserved
fast last past cast blast contrast forecast
deep sleep creep leap keep reap steep
truth proof youth booth uncouth
""".split()

def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    try:
        import pronouncing
        count = pronouncing.syllable_count(w)
        if count:
            return count
    except Exception:
        pass
    groups = re.findall(r"[aeiouy]+", w)
    count = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ye")) and count > 1:
        count -= 1
    if w.endswith("es") and not w.endswith(("ses", "xes", "zes", "ches", "shes")) and count > 1:
        count -= 1
    return max(1, count)

def rhyme_key(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if len(w) < 3:
        return w[-1:]
    # Lightweight spelling-based approximation; pronouncing is preferred.
    for n in (4, 3, 2):
        if len(w) >= n:
            return w[-n:]
    return w

def find_rhymes(target, count=30, multi=False):
    target = target.strip().lower()
    if not target:
        return []
    try:
        import pronouncing
        phones = pronouncing.phones_for_word(target)
        if phones:
            rhymes = pronouncing.rhymes(target)
            if rhymes:
                return sorted(set(rhymes), key=lambda x: (abs(syllables(x)-syllables(target)), x))[:count]
    except Exception:
        pass
    words = set(SEED_WORDS)
    # Add common user words from the current draft.
    return sorted((w for w in words if w != target and rhyme_key(w) == rhyme_key(target)),
                  key=lambda x: (abs(syllables(x)-syllables(target)), x))[:count]

class Splash(QWidget):
    def __init__(self, done):
        super().__init__()
        self.done = done
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(760, 430)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.title = QLabel("Created by DJ", self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setGeometry(30, 120, 700, 90)
        self.title.setStyleSheet("color:#f7f7fb;font-size:42px;font-weight:900;letter-spacing:3px;")
        self.sub = QLabel("THE ULTIMATE RAPPAD", self)
        self.sub.setAlignment(Qt.AlignCenter)
        self.sub.setGeometry(30, 205, 700, 35)
        self.sub.setStyleSheet("color:#a8a8bd;font-size:13px;font-weight:700;letter-spacing:5px;")
        self.center()
        QTimer.singleShot(1450, self.show_enjoy)

    def center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x()-self.width()//2, screen.center().y()-self.height()//2)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor("#10101b"))
        grad.setColorAt(0.55, QColor("#1b1230"))
        grad.setColorAt(1, QColor("#081a25"))
        p.setBrush(grad); p.setPen(Qt.NoPen); p.drawRoundedRect(self.rect(), 24, 24)
        p.setPen(QPen(QColor("#9d4dff"), 2)); p.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 24, 24)
        p.setPen(QPen(QColor(0, 229, 255, 55), 1))
        for x in range(25, self.width(), 38): p.drawLine(x, 0, x, self.height())
        for y in range(20, self.height(), 38): p.drawLine(0, y, self.width(), y)

    def show_enjoy(self):
        self.title.setText("Enjoy!")
        self.sub.setText("YOUR WORDS. YOUR FLOW. YOUR SOUND.")
        QTimer.singleShot(1000, self.fade_out)

    def fade_out(self):
        anim = QPropertyAnimation(self.opacity, b"opacity", self)
        anim.setDuration(650); anim.setStartValue(1.0); anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(self.finish)
        anim.start()
        self.anim = anim

    def finish(self):
        self.close()
        self.done()

class NavButton(QPushButton):
    def __init__(self, text, page, callback):
        super().__init__(text)
        self.page = page
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.clicked.connect(lambda: callback(page))


class UpdateWorker(QThread):
    result = Signal(bool, str, str)
    def run(self):
        try:
            cfg = json.loads(UPDATE_CONFIG.read_text(encoding="utf-8")) if UPDATE_CONFIG.exists() else {}
            owner, repo = cfg.get("github_owner", ""), cfg.get("github_repo", "")
            if not owner or not repo or "YOUR_" in owner or "YOUR_" in repo:
                self.result.emit(False, "Updater needs your GitHub repository configured in update_config.json.", "")
                return
            api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            req = urllib.request.Request(api, headers={"User-Agent":"UltimateRapPad-Updater","Accept":"application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=15) as response:
                release = json.loads(response.read().decode("utf-8"))
            tag = release.get("tag_name", "").lstrip("v")
            if not tag:
                self.result.emit(False, "GitHub did not return a release version.", "")
                return
            def ver_tuple(v):
                try: return tuple(int(x) for x in re.findall(r"\d+", v)[:3])
                except Exception: return (0,)
            if ver_tuple(tag) <= ver_tuple(APP_VERSION):
                self.result.emit(True, f"You're up to date. Current version: {APP_VERSION}", "")
                return
            asset = next((a for a in release.get("assets", []) if a.get("name") == "UltimateRapPad-Windows.zip"), None)
            if not asset:
                self.result.emit(False, "A newer release exists, but its UltimateRapPad-Windows.zip asset is missing.", "")
                return
            temp_dir = Path(tempfile.mkdtemp(prefix="UltimateRapPadUpdate_"))
            zip_path = temp_dir / "update.zip"
            req = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent":"UltimateRapPad-Updater"})
            with urllib.request.urlopen(req, timeout=60) as response, open(zip_path, "wb") as out:
                shutil.copyfileobj(response, out)
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir()
            with zipfile.ZipFile(zip_path) as zf: zf.extractall(extract_dir)
            candidates = list(extract_dir.rglob("UltimateRapPad.exe"))
            if not candidates:
                self.result.emit(False, "Update downloaded, but UltimateRapPad.exe was not found in the release ZIP.", "")
                return
            self.result.emit(True, f"Version {tag} downloaded. Preparing to install...", str(candidates[0]))
        except urllib.error.HTTPError as e:
            self.result.emit(False, f"GitHub returned HTTP {e.code}. Check repository visibility and release settings.", "")
        except Exception as e:
            self.result.emit(False, f"Update check failed: {e}", "")

class RapPad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1420, 900)
        self.setMinimumSize(1080, 700)
        self.current_file = None
        self.bpm = 92
        self.metronome_on = False
        self.beat_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.live_rhyme_timer = QTimer(self)
        self.live_rhyme_timer.setSingleShot(True)
        self.live_rhyme_timer.setInterval(220)
        self.live_rhyme_timer.timeout.connect(self.update_live_rhymes)
        self.pages = QStackedWidget()
        self.nav_buttons = []
        self.build_ui()
        self.load_autosave()
        self.apply_style()

    def build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        outer = QHBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(238)
        side = QVBoxLayout(sidebar); side.setContentsMargins(18,25,18,20); side.setSpacing(10)
        logo = QLabel("URP<span>●</span>")
        logo.setText("URP  /  RAP LAB")
        logo.setObjectName("logo"); side.addWidget(logo)
        tagline = QLabel("WRITE WITHOUT LIMITS"); tagline.setObjectName("tagline"); side.addWidget(tagline)
        side.addSpacing(28)
        nav_items = [("✦   Studio",0),("⌁   Rhyme Lab",1),("▤   Word Vault",2),("◉   Flow & Tempo",3),("▣   Song Library",4)]
        for label, page in nav_items:
            b = NavButton(label,page,self.navigate); self.nav_buttons.append(b); side.addWidget(b)
        side.addStretch()
        self.status = QLabel("●  LOCAL WORKSPACE"); self.status.setObjectName("status"); side.addWidget(self.status)
        ver = QLabel("ULTIMATE RAPPAD  •  v2.0"); ver.setObjectName("version"); side.addWidget(ver)
        outer.addWidget(sidebar)
        main = QVBoxLayout(); main.setContentsMargins(28,22,28,24); main.setSpacing(16)
        outer.addLayout(main,1)
        top = QHBoxLayout()
        self.page_title = QLabel("STUDIO"); self.page_title.setObjectName("pageTitle"); top.addWidget(self.page_title)
        top.addStretch()
        self.update_btn = QPushButton("CHECK FOR UPDATES")
        self.update_btn.clicked.connect(self.check_for_updates)
        top.addWidget(self.update_btn)
        self.save_btn = QPushButton("SAVE SESSION"); self.save_btn.clicked.connect(self.save_session); top.addWidget(self.save_btn)
        self.open_btn = QPushButton("OPEN"); self.open_btn.clicked.connect(self.open_session); top.addWidget(self.open_btn)
        main.addLayout(top)
        self.pages.addWidget(self.make_studio())
        self.pages.addWidget(self.make_rhyme_lab())
        self.pages.addWidget(self.make_word_vault())
        self.pages.addWidget(self.make_flow())
        self.pages.addWidget(self.make_library())
        main.addWidget(self.pages,1)
        self.navigate(0)

    def panel(self, title, subtitle=""):
        frame = QFrame(); frame.setObjectName("panel")
        lay = QVBoxLayout(frame); lay.setContentsMargins(18,16,18,18); lay.setSpacing(10)
        head = QHBoxLayout()
        label = QLabel(title); label.setObjectName("panelTitle"); head.addWidget(label)
        head.addStretch()
        if subtitle:
            sub = QLabel(subtitle); sub.setObjectName("muted"); head.addWidget(sub)
        lay.addLayout(head)
        return frame, lay

    def make_studio(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0,0,0,0); layout.setSpacing(14)
        stats = QHBoxLayout()
        for big, small in [("16 BAR","VERSE BUILDER"),("∞","IDEAS ALLOWED"),("LOCAL","PRIVATE BY DESIGN")]:
            card = QFrame(); card.setObjectName("stat")
            v=QVBoxLayout(card); a=QLabel(big); a.setObjectName("statBig"); b=QLabel(small); b.setObjectName("statSmall"); v.addWidget(a); v.addWidget(b); stats.addWidget(card)
        layout.addLayout(stats)
        split = QSplitter(Qt.Horizontal)
        editor_frame, ev = self.panel("LYRIC CANVAS","LIVE WRITING")
        toolbar=QHBoxLayout()
        self.song_title=QLineEdit(); self.song_title.setPlaceholderText("Untitled session")
        self.scheme=QComboBox(); self.scheme.addItems(["Freeform","AABB","ABAB","AAAA","ABBA","Internal / dense"])
        toolbar.addWidget(self.song_title,2); toolbar.addWidget(QLabel("SCHEME")); toolbar.addWidget(self.scheme,1)
        ev.addLayout(toolbar)
        self.editor=QTextEdit(); self.editor.setPlaceholderText("Start with a line. Build a pocket. Make every syllable count.\n\n[Verse 1]\n"); self.editor.setObjectName("editor")
        ev.addWidget(self.editor,1)
        foot=QHBoxLayout()
        self.word_count=QLabel("0 words  •  0 lines"); self.word_count.setObjectName("muted")
        self.editor.textChanged.connect(self.update_counts)
        foot.addWidget(self.word_count); foot.addStretch()
        clear=QPushButton("CLEAR"); clear.clicked.connect(self.clear_editor); foot.addWidget(clear)
        ev.addLayout(foot)
        split.addWidget(editor_frame)
        right=QWidget(); rv=QVBoxLayout(right); rv.setContentsMargins(0,0,0,0); rv.setSpacing(14)
        tools, tl=self.panel("LIVE RHYME ENGINE","AUTO-DETECTING LAST WORD")
        self.live_target=QLabel("Start writing to see rhyme suggestions.")
        self.live_target.setObjectName("muted")
        self.live_results=QListWidget()
        self.live_results.itemDoubleClicked.connect(self.insert_live_rhyme)
        self.live_results.setMinimumHeight(190)
        self.live_mode=QComboBox()
        self.live_mode.addItems(["Closest syllable match","All rhyme matches"])
        self.live_mode.currentIndexChanged.connect(lambda: self.live_rhyme_timer.start())
        tl.addWidget(self.live_target)
        tl.addWidget(self.live_mode)
        tl.addWidget(self.live_results,1)
        rv.addWidget(tools,2)
        prompt, pl=self.panel("WRITER'S PROMPT","BEAT THE BLANK PAGE")
        self.prompt_label=QLabel("Flip a prompt when you need a new angle."); self.prompt_label.setWordWrap(True); self.prompt_label.setObjectName("prompt")
        pb=QPushButton("GENERATE PROMPT"); pb.clicked.connect(self.new_prompt)
        pl.addWidget(self.prompt_label); pl.addWidget(pb)
        rv.addWidget(prompt,1)
        split.addWidget(right); split.setSizes([760,360])
        layout.addWidget(split,1)
        return page

    def make_rhyme_lab(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(0,0,0,0)
        top, t=self.panel("PHONETIC RHYME FINDER","SINGLE WORD • MULTI-SYLLABLE • NEAR RHYMES")
        row=QHBoxLayout(); self.rhyme_input=QLineEdit(); self.rhyme_input.setPlaceholderText("Type a target word, e.g. 'elevation'"); self.rhyme_input.returnPressed.connect(self.run_rhymes)
        self.rhyme_count=QSpinBox(); self.rhyme_count.setRange(5,100); self.rhyme_count.setValue(35)
        btn=QPushButton("SEARCH RHYMES"); btn.clicked.connect(self.run_rhymes)
        row.addWidget(self.rhyme_input,1); row.addWidget(QLabel("RESULTS")); row.addWidget(self.rhyme_count); row.addWidget(btn)
        t.addLayout(row)
        self.rhyme_results=QListWidget(); self.rhyme_results.setObjectName("results")
        self.rhyme_results.itemDoubleClicked.connect(self.insert_rhyme)
        t.addWidget(self.rhyme_results,1)
        note=QLabel("Tip: install the optional 'pronouncing' package for a much larger CMU pronunciation dictionary. Double-click a result to drop it into your lyric canvas.")
        note.setObjectName("muted"); note.setWordWrap(True); t.addWidget(note)
        layout.addWidget(top,1); return page

    def make_word_vault(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(0,0,0,0)
        frame, v=self.panel("WORD VAULT","YOUR PERSONAL AMMUNITION")
        row=QHBoxLayout(); self.vault_input=QLineEdit(); self.vault_input.setPlaceholderText("Add a word, phrase, punchline seed, or image...")
        add=QPushButton("ADD TO VAULT"); add.clicked.connect(self.add_vault)
        row.addWidget(self.vault_input,1); row.addWidget(add); v.addLayout(row)
        self.vault_list=QListWidget(); self.vault_list.itemDoubleClicked.connect(self.insert_vault)
        v.addWidget(self.vault_list,1)
        controls=QHBoxLayout(); remove=QPushButton("REMOVE SELECTED"); remove.clicked.connect(lambda: self.remove_selected(self.vault_list))
        controls.addWidget(remove); controls.addStretch(); controls.addWidget(QLabel("Double-click an entry to insert it into the canvas."))
        v.addLayout(controls); layout.addWidget(frame,1); return page

    def make_flow(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(0,0,0,0)
        frame, v=self.panel("FLOW & TEMPO","BUILD A POCKET")
        bpmrow=QHBoxLayout(); bpmrow.addWidget(QLabel("TEMPO"))
        self.bpm_value=QLabel("92 BPM"); self.bpm_value.setObjectName("statBig"); bpmrow.addWidget(self.bpm_value)
        self.bpm_slider=QSlider(Qt.Horizontal); self.bpm_slider.setRange(40,220); self.bpm_slider.setValue(92); self.bpm_slider.valueChanged.connect(self.change_bpm)
        bpmrow.addWidget(self.bpm_slider,1); v.addLayout(bpmrow)
        actions=QHBoxLayout(); self.metro_btn=QPushButton("START METRONOME"); self.metro_btn.clicked.connect(self.toggle_metronome); actions.addWidget(self.metro_btn)
        self.beat_label=QLabel("READY"); self.beat_label.setObjectName("beat"); actions.addWidget(self.beat_label); actions.addStretch(); v.addLayout(actions)
        self.beat_grid=QGridLayout()
        self.beat_dots=[]
        for i in range(16):
            dot=QLabel(str((i%4)+1)); dot.setAlignment(Qt.AlignCenter); dot.setObjectName("beatDot"); self.beat_dots.append(dot); self.beat_grid.addWidget(dot,i//4,i%4)
        v.addLayout(self.beat_grid)
        v.addWidget(QLabel("FLOW DRILLS"))
        drillrow=QHBoxLayout()
        self.drill_combo=QComboBox(); self.drill_combo.addItems(["Triplet pocket","Double-time burst","Pause and punch","Internal rhyme ladder","Four-bar storytelling"])
        drill=QPushButton("GIVE ME A DRILL"); drill.clicked.connect(self.make_drill)
        drillrow.addWidget(self.drill_combo,1); drillrow.addWidget(drill); v.addLayout(drillrow)
        self.drill_text=QTextEdit(); self.drill_text.setReadOnly(True); self.drill_text.setMaximumHeight(180); self.drill_text.setPlaceholderText("Your next flow exercise will appear here.")
        v.addWidget(self.drill_text)
        layout.addWidget(frame,1); return page

    def make_library(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(0,0,0,0)
        frame,v=self.panel("SONG LIBRARY","YOUR SESSIONS, ALL IN ONE PLACE")
        self.library_list=QListWidget(); self.library_list.itemDoubleClicked.connect(self.load_library_item); v.addWidget(self.library_list,1)
        row=QHBoxLayout(); refresh=QPushButton("REFRESH"); refresh.clicked.connect(self.refresh_library)
        load=QPushButton("LOAD SELECTED"); load.clicked.connect(self.load_library_selected)
        row.addWidget(refresh); row.addWidget(load); row.addStretch(); v.addLayout(row)
        layout.addWidget(frame,1); self.refresh_library(); return page

    def navigate(self, page):
        self.pages.setCurrentIndex(page)
        names=["STUDIO","RHYME LAB","WORD VAULT","FLOW & TEMPO","SONG LIBRARY"]
        self.page_title.setText(names[page])
        for b in self.nav_buttons: b.setChecked(b.page==page)

    def update_counts(self):
        txt=self.editor.toPlainText()
        words=re.findall(r"\b[\w']+\b",txt)
        lines=[x for x in txt.splitlines() if x.strip()]
        self.word_count.setText(f"{len(words)} words  •  {len(lines)} lines  •  {len(txt)} characters")


    def update_live_rhymes(self):
        if not hasattr(self, "editor") or not hasattr(self, "live_results"):
            return
        current_line = self.editor.textCursor().block().text()
        words = re.findall(r"[A-Za-z']+", current_line)
        if not words:
            self.live_target.setText("Waiting for your next line...")
            self.live_results.clear()
            return
        target = words[-1].strip("'").lower()
        self.live_target.setText(f"RHYMES FOR:  {target.upper()}   •   {syllables(target)} syllable(s)")
        self.live_results.clear()
        matches = find_rhymes(target, 60 if self.live_mode.currentIndex() else 30)
        if self.live_mode.currentIndex() == 0:
            target_syllables = syllables(target)
            matches = sorted(matches, key=lambda w: (abs(syllables(w)-target_syllables), w))
        for word in matches[:30]:
            item = QListWidgetItem(f"{word}     •     {syllables(word)} syl")
            item.setData(Qt.UserRole, word)
            self.live_results.addItem(item)
        if not matches:
            self.live_results.addItem("No match in the current pronunciation dictionary.")
    def insert_live_rhyme(self, item):
        word = item.data(Qt.UserRole)
        if not word:
            return
        cursor = self.editor.textCursor()
        cursor.insertText(word)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def quick_rhyme(self):
        word=self.quick_word.text().strip()
        self.quick_results.clear()
        for r in find_rhymes(word,20): self.quick_results.addItem(r)
        if not self.quick_results.count(): self.quick_results.addItem("No matches in the compact offline word bank.")

    def run_rhymes(self):
        word=self.rhyme_input.text().strip()
        self.rhyme_results.clear()
        if not word: return
        results=find_rhymes(word,self.rhyme_count.value())
        if not results: self.rhyme_results.addItem("No matches found. Try another word or install pronouncing.")
        else:
            for r in results:
                item=QListWidgetItem(f"{r}     •     {syllables(r)} syllable(s)")
                item.setData(Qt.UserRole,r); self.rhyme_results.addItem(item)

    def insert_rhyme(self,item):
        word=item.data(Qt.UserRole) or item.text().split()[0]
        self.editor.insertPlainText(word+" "); self.navigate(0)

    def add_vault(self):
        value=self.vault_input.text().strip()
        if value:
            self.vault_list.addItem(value); self.vault_input.clear()

    def insert_vault(self,item):
        self.editor.insertPlainText(item.text()+" "); self.navigate(0)

    def remove_selected(self, widget):
        row=widget.currentRow()
        if row>=0: widget.takeItem(row)

    def clear_editor(self):
        if QMessageBox.question(self,"Clear canvas","Clear the current lyric canvas?") == QMessageBox.Yes:
            self.editor.clear()

    def new_prompt(self):
        prompts=[
            "Write four bars where every line changes the meaning of the line before it.",
            "Describe your biggest obstacle without naming it. Let the images reveal it.",
            "Build a verse around one object in the room. Give it a hidden double meaning.",
            "Write a confident 8-bar run using one multisyllabic rhyme family throughout.",
            "Tell a true story in reverse: begin with the consequence, then reveal the cause.",
            "Use a quiet first line, then make the fourth line hit like a door kicked open.",
            "Write a hook with a phrase people can remember after one listen.",
            "Create a 4-bar scheme where the internal rhyme lands before the end rhyme."
        ]
        self.prompt_label.setText(random.choice(prompts))

    def change_bpm(self,value):
        self.bpm=value; self.bpm_value.setText(f"{value} BPM")
        if self.timer.isActive(): self.timer.start(int(60000/value/4))

    def toggle_metronome(self):
        if self.timer.isActive():
            self.timer.stop(); self.metro_btn.setText("START METRONOME"); self.beat_label.setText("PAUSED")
        else:
            self.beat_count=0; self.timer.start(int(60000/self.bpm/4)); self.metro_btn.setText("STOP METRONOME"); self.beat_label.setText("PLAYING")

    def tick(self):
        self.beat_count=(self.beat_count+1)%16
        for i,dot in enumerate(self.beat_dots): dot.setProperty("active",i==self.beat_count)
        self.beat_label.setText(f"STEP {self.beat_count+1:02d} / 16")
        self.style().unpolish(self); self.style().polish(self)

    def make_drill(self):
        drills={
          "Triplet pocket":"Write 4 bars with a da-da-DUM pulse. Keep each bar in groups of three syllables, then vary the final group.",
          "Double-time burst":"Write 2 bars with 12–16 syllables each. Keep consonants crisp, then leave a full beat of space.",
          "Pause and punch":"Write a setup line, mark a pause with [REST], then land the strongest word after the silence.",
          "Internal rhyme ladder":"Choose one sound. Place it twice inside each line and once at the end. Escalate the imagery every bar.",
          "Four-bar storytelling":"Bar 1: establish place. Bar 2: introduce a problem. Bar 3: make a choice. Bar 4: reveal the cost."
        }
        self.drill_text.setPlainText(drills[self.drill_combo.currentText()])


    def check_for_updates(self):
        if getattr(sys, "frozen", False) is False:
            QMessageBox.information(self, "Build required",
                "The one-click updater is enabled in the packaged Windows EXE.\\n\\n"
                "You're currently running from Python source. Build the EXE first, then configure update_config.json.")
            return
        self.update_btn.setEnabled(False)
        self.update_btn.setText("CHECKING...")
        self.update_worker = UpdateWorker()
        self.update_worker.result.connect(self.finish_update_check)
        self.update_worker.start()

    def finish_update_check(self, ok, message, new_exe):
        self.update_btn.setEnabled(True)
        self.update_btn.setText("CHECK FOR UPDATES")
        if not ok or not new_exe:
            QMessageBox.information(self, "Ultimate RapPad Updater", message)
            return
        helper = Path(sys.executable).with_name("RapPadUpdater.exe")
        if not helper.exists():
            helper = Path(__file__).with_name("update_helper.py")
        if helper.suffix.lower() == ".py":
            args = [sys.executable, str(helper), sys.executable, new_exe, str(os.getpid())]
        else:
            args = [str(helper), sys.executable, new_exe, str(os.getpid())]
        QMessageBox.information(self, "Update ready", message + "\\n\\nThe app will close, update, and restart.")
        subprocess.Popen(args, close_fds=True)
        QApplication.quit()

    def session_data(self):
        return {"title":self.song_title.text(),"lyrics":self.editor.toPlainText(),"scheme":self.scheme.currentText(),
                "vault":[self.vault_list.item(i).text() for i in range(self.vault_list.count())],"bpm":self.bpm}

    def apply_data(self,data):
        self.song_title.setText(data.get("title","")); self.editor.setPlainText(data.get("lyrics",""))
        self.scheme.setCurrentText(data.get("scheme","Freeform")); self.vault_list.clear()
        self.vault_list.addItems(data.get("vault",[])); self.bpm_slider.setValue(int(data.get("bpm",92)))

    def save_session(self):
        data=self.session_data()
        default=(re.sub(r"[^A-Za-z0-9_-]+","_",data["title"]).strip("_") or "rap_session")+".json"
        path,_=QFileDialog.getSaveFileName(self,"Save Rap Session",str(DATA_DIR/default),"RapPad Session (*.json)")
        if not path: return
        try:
            Path(path).write_text(json.dumps(data,indent=2),encoding="utf-8")
            self.status.setText("●  SESSION SAVED"); self.refresh_library()
        except Exception as e: QMessageBox.critical(self,"Save failed",str(e))

    def open_session(self):
        path,_=QFileDialog.getOpenFileName(self,"Open Rap Session",str(DATA_DIR),"RapPad Session (*.json)")
        if path:
            try: self.apply_data(json.loads(Path(path).read_text(encoding="utf-8"))); self.current_file=path
            except Exception as e: QMessageBox.critical(self,"Open failed",str(e))

    def load_autosave(self):
        try:
            if AUTOSAVE.exists(): self.apply_data(json.loads(AUTOSAVE.read_text(encoding="utf-8")))
        except Exception: pass

    def closeEvent(self,event):
        try: AUTOSAVE.write_text(json.dumps(self.session_data(),indent=2),encoding="utf-8")
        except Exception: pass
        if self.timer.isActive(): self.timer.stop()
        event.accept()

    def refresh_library(self):
        self.library_list.clear()
        for p in sorted(DATA_DIR.glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
            if p.name=="autosave.json": continue
            self.library_list.addItem(QListWidgetItem(p.name))

    def load_library_item(self,item):
        self.load_library_file(item.text())

    def load_library_selected(self):
        item=self.library_list.currentItem()
        if item: self.load_library_file(item.text())

    def load_library_file(self,name):
        path=DATA_DIR/name
        try: self.apply_data(json.loads(path.read_text(encoding="utf-8"))); self.navigate(0)
        except Exception as e: QMessageBox.critical(self,"Load failed",str(e))

    def apply_style(self):
        self.setStyleSheet("""
        QWidget { background:#0b0c14; color:#e9e9f2; font-family:'Segoe UI'; font-size:13px; }
        #sidebar { background:#10111c; border-right:1px solid #25263a; }
        #logo { color:#f5f4ff; font-size:22px; font-weight:900; letter-spacing:2px; }
        #tagline,#version { color:#777990; font-size:9px; letter-spacing:2px; font-weight:700; }
        #status { color:#50e3c2; font-size:10px; font-weight:700; }
        QPushButton { background:#1c1e2d; border:1px solid #303249; border-radius:8px; padding:10px 14px; color:#e7e7f1; font-weight:700; }
        QPushButton:hover { background:#29233e; border-color:#a855f7; }
        QPushButton:checked { background:#542d85; border-color:#bd7aff; color:white; }
        #pageTitle { font-size:22px; font-weight:900; letter-spacing:3px; color:#f5f4ff; }
        #panel { background:#121421; border:1px solid #282a40; border-radius:14px; }
        #panelTitle { font-size:13px; font-weight:900; letter-spacing:2px; color:#f2f0ff; }
        #muted { color:#8588a2; font-size:11px; }
        #stat { background:#151727; border:1px solid #292b42; border-radius:12px; padding:12px; }
        #statBig { color:#bd7aff; font-size:22px; font-weight:900; }
        #statSmall { color:#888ba4; font-size:9px; font-weight:800; letter-spacing:2px; }
        QLineEdit,QComboBox,QSpinBox { background:#0d0f19; border:1px solid #34364d; border-radius:7px; padding:10px; color:#f2f2fa; }
        QTextEdit { background:#0d0f19; border:1px solid #303249; border-radius:9px; padding:12px; selection-background-color:#673ab7; }
        #editor { font-family:Consolas; font-size:15px; line-height:1.5; }
        QListWidget { background:#0d0f19; border:1px solid #303249; border-radius:8px; padding:6px; }
        QListWidget::item { padding:9px; border-radius:5px; }
        QListWidget::item:selected { background:#43266a; }
        #prompt { color:#d7c4f5; font-size:15px; padding:8px; }
        #liveTarget { color:#50e3c2; font-weight:800; }
        #beat { color:#50e3c2; font-size:15px; font-weight:900; letter-spacing:2px; }
        #beatDot { background:#202236; border:1px solid #393c56; border-radius:9px; min-height:58px; font-size:18px; font-weight:900; color:#888ba4; }
        #beatDot[active="true"] { background:#6936a6; border:2px solid #d1a3ff; color:white; }
        QSlider::groove:horizontal { height:6px; background:#292b40; border-radius:3px; }
        QSlider::handle:horizontal { background:#bd7aff; width:18px; margin:-7px 0; border-radius:9px; }
        """)
        for b in self.nav_buttons:
            b.setStyleSheet("text-align:left;padding:13px;border:0;border-radius:8px;color:#b9bbce;")

def main():
    app=QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    font=QFont("Segoe UI",10); app.setFont(font)
    window=RapPad()
    def launch():
        window.show()
    splash=Splash(launch); splash.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
