"""Beginner learning module: a card grid that opens interactive lessons.

The grid borrows the course-card idea but uses the app's own visual language.
A lesson opens as a centred board with the explanation underneath, never the
board-left / panel-right layout used by the other modules.
"""

import chess
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from checkpause.core.lesson import INFO, MOVE, LessonSession
from checkpause.data.learn import load_progress, save_lesson_progress
from checkpause.data.lessons import SECTIONS, load_lessons
from checkpause.gui.icons import action_icon
from checkpause.gui.theme import DARK, LIGHT
from checkpause.gui.widgets.board import BoardWidget
from checkpause.i18n import t

LEARN_TONES = {
    LIGHT: {
        "pieces": "#4a657f",
        "basics": "#4f7863",
        "advanced": "#8a6a3f",
        "mates": "#7a536e",
    },
    DARK: {
        "pieces": "#5d7f9d",
        "basics": "#5f8f77",
        "advanced": "#a17f4f",
        "mates": "#946b85",
    },
}


class _LearnCard(QFrame):
    clicked = Signal(str)

    def __init__(self, lesson, theme, language, parent=None):
        super().__init__(parent)
        self._lesson = lesson
        self._theme = theme
        self._language = language
        self._entry = {}
        self.setObjectName("learnCard")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(84)

        self._icon = QLabel()
        self._icon.setFixedSize(54, 54)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._title = QLabel()
        self._title.setObjectName("learnCardTitle")
        self._title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._subtitle = QLabel()
        self._subtitle.setObjectName("learnCardSubtitle")
        self._subtitle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._badge = QLabel()
        self._badge.setObjectName("learnBadge")
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)
        text_layout.addWidget(self._title)
        text_layout.addWidget(self._subtitle)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)
        layout.addWidget(self._icon)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignTop)

        self.apply_theme(theme)
        self.retranslate(language)

    def apply_theme(self, theme):
        self._theme = theme
        tone = LEARN_TONES.get(theme, LEARN_TONES[LIGHT]).get(self._lesson.section, "#4a657f")
        self._icon.setStyleSheet(f"background-color: {tone}; border-radius: 14px;")
        icon = action_icon(theme, self._lesson.icon, size=26, color="#ffffff")
        self._icon.setPixmap(icon.pixmap(QSize(26, 26)))

    def retranslate(self, language):
        self._language = language
        self._title.setText(t(self._lesson.title_key, language))
        self._subtitle.setText(t(self._lesson.subtitle_key, language))
        self._refresh_badge()

    def set_status(self, entry):
        self._entry = entry or {}
        self._refresh_badge()

    def _refresh_badge(self):
        total = len(self._lesson.steps)
        completed = bool(self._entry.get("completed"))
        try:
            step = int(self._entry.get("step", 0))
        except (TypeError, ValueError):
            step = 0
        if completed:
            status = "done"
            text = t("learn_status_done", self._language)
        elif step > 0:
            status = "active"
            text = t(
                "learn_status_progress",
                self._language,
                done=min(step, total),
                total=total,
            )
        else:
            status = "new"
            text = t("learn_status_start", self._language)
        self._badge.setText(text)
        self._badge.setProperty("status", status)
        self._badge.style().unpolish(self._badge)
        self._badge.style().polish(self._badge)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self.clicked.emit(self._lesson.id)
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        ):
            self.clicked.emit(self._lesson.id)
            return
        super().keyPressEvent(event)


class LearnPage(QWidget):
    def __init__(self, parent=None, progress_base_dir=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._theme = LIGHT
        self._progress_base_dir = progress_base_dir
        self._lessons = load_lessons()
        self._by_id = {lesson.id: lesson for lesson in self._lessons}
        self._progress = load_progress(progress_base_dir)
        self._cards = {}
        self._session = None
        self._active_lesson = None
        self._feedback_state = ""
        self._replaying = False

        self._stack = QStackedWidget(self)
        self._grid_view = self._build_grid()
        self._detail_view = self._build_detail()
        self._stack.addWidget(self._grid_view)
        self._stack.addWidget(self._detail_view)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

        self._apply_icons()
        self.retranslate(self._language)

    def _build_grid(self):
        scroll = QScrollArea()
        scroll.setObjectName("learnScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        inner.setObjectName("learnPage")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(18)

        self._header_title = QLabel()
        self._header_title.setObjectName("learnHeaderTitle")
        self._header_subtitle = QLabel()
        self._header_subtitle.setObjectName("learnHeaderSubtitle")
        self._header_progress = QLabel()
        self._header_progress.setObjectName("learnHeaderProgress")

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(4)
        title_box.addWidget(self._header_title)
        title_box.addWidget(self._header_subtitle)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 6)
        header.addLayout(title_box, 1)
        header.addWidget(
            self._header_progress,
            0,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        layout.addLayout(header)

        for section in SECTIONS:
            section_label = QLabel()
            section_label.setObjectName("learnSectionLabel")
            section_label.setProperty("title_key", section["title_key"])
            layout.addWidget(section_label)

            grid = QGridLayout()
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(14)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)
            section_lessons = [
                lesson for lesson in self._lessons if lesson.section == section["id"]
            ]
            for index, lesson in enumerate(section_lessons):
                card = _LearnCard(lesson, self._theme, self._language)
                card.clicked.connect(self.show_lesson)
                card.set_status(self._progress.get(lesson.id))
                self._cards[lesson.id] = card
                grid.addWidget(card, index // 2, index % 2)
            layout.addLayout(grid)

        layout.addStretch(1)
        scroll.setWidget(inner)
        return scroll

    def _build_detail(self):
        view = QWidget()
        view.setObjectName("learnDetail")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(28, 18, 28, 22)
        layout.setSpacing(12)

        self._btn_back = QPushButton()
        self._btn_back.setObjectName("learnBackButton")
        self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_back.clicked.connect(self._back_to_grid)

        self._lesson_title = QLabel()
        self._lesson_title.setObjectName("learnLessonTitle")
        self._lesson_subtitle = QLabel()
        self._lesson_subtitle.setObjectName("learnLessonSubtitle")

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(2)
        title_box.addWidget(self._lesson_title)
        title_box.addWidget(self._lesson_subtitle)

        self._step_label = QLabel()
        self._step_label.setObjectName("learnStepLabel")
        self._step_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)
        header.addWidget(self._btn_back)
        header.addLayout(title_box, 1)
        header.addWidget(self._step_label)
        layout.addLayout(header)

        self._step_progress = QProgressBar()
        self._step_progress.setObjectName("learnProgress")
        self._step_progress.setTextVisible(False)
        self._step_progress.setRange(0, 1)
        self._step_progress.setValue(0)
        layout.addWidget(self._step_progress)

        self._board = BoardWidget()
        self._board.set_lesson_mode(True)
        self._board.setMinimumWidth(360)
        self._board.setMaximumWidth(600)
        self._board.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._board.move_requested.connect(self._on_move_requested)

        board_row = QHBoxLayout()
        board_row.setContentsMargins(0, 0, 0, 0)
        board_row.addStretch(1)
        board_row.addWidget(self._board, 6)
        board_row.addStretch(1)
        layout.addLayout(board_row, 1)

        panel = QFrame()
        panel.setObjectName("learnPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 14, 18, 14)
        panel_layout.setSpacing(8)

        self._instruction = QLabel()
        self._instruction.setObjectName("learnInstruction")
        self._instruction.setWordWrap(True)
        self._feedback = QLabel()
        self._feedback.setObjectName("learnFeedback")
        self._feedback.setWordWrap(True)

        self._btn_hint = QPushButton()
        self._btn_hint.setObjectName("learnHintButton")
        self._btn_hint.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_hint.clicked.connect(self._on_hint)
        self._btn_retry = QPushButton()
        self._btn_retry.setObjectName("learnRetryButton")
        self._btn_retry.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_retry.clicked.connect(self._on_retry)
        self._btn_primary = QPushButton()
        self._btn_primary.setObjectName("learnPrimaryButton")
        self._btn_primary.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_primary.clicked.connect(self._on_primary)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)
        buttons.addWidget(self._btn_hint)
        buttons.addWidget(self._btn_retry)
        buttons.addStretch(1)
        buttons.addWidget(self._btn_primary)

        panel_layout.addWidget(self._instruction)
        panel_layout.addWidget(self._feedback)
        panel_layout.addLayout(buttons)
        layout.addWidget(panel)
        return view

    def _apply_icons(self):
        self._btn_back.setIcon(action_icon(self._theme, "nav_prev"))
        self._btn_back.setIconSize(QSize(16, 16))
        self._btn_hint.setIcon(action_icon(self._theme, "hint"))
        self._btn_hint.setIconSize(QSize(14, 14))
        self._btn_retry.setIcon(action_icon(self._theme, "reset"))
        self._btn_retry.setIconSize(QSize(14, 14))

    def set_theme(self, theme):
        self._theme = theme
        self._apply_icons()
        self._board.set_theme(theme)
        for card in self._cards.values():
            card.apply_theme(theme)

    def set_piece_set(self, name):
        self._board.set_piece_set(name)

    def set_board_theme(self, name):
        self._board.set_board_theme(name)

    def set_sound_set(self, name):
        self._board.set_sound_set(name)

    def set_sound_enabled(self, enabled):
        self._board.set_sound_enabled(enabled)

    def retranslate(self, language):
        self._language = language
        self._header_title.setText(t("learn_title", language))
        self._header_subtitle.setText(t("learn_subtitle", language))
        for card in self._cards.values():
            card.retranslate(language)
        self._refresh_header_progress()

        self._btn_back.setText(t("learn_back", language))
        self._btn_hint.setText(t("learn_hint", language))
        self._btn_retry.setText(t("learn_retry", language))
        self._btn_primary.setText(t("learn_continue", language))

        scroll = self._grid_view
        inner = scroll.widget()
        if inner is not None:
            for label in inner.findChildren(QLabel, "learnSectionLabel"):
                key = label.property("title_key")
                if key:
                    label.setText(t(key, language))

        if self._session is not None:
            if self._session.completed:
                self._render_complete()
            else:
                self._render_step()

    def show_lesson(self, lesson_id):
        lesson = self._by_id.get(lesson_id)
        if lesson is None:
            return
        entry = self._progress.get(lesson.id, {})
        start = 0
        if not entry.get("completed"):
            try:
                start = int(entry.get("step", 0))
            except (TypeError, ValueError):
                start = 0
            start = max(0, min(start, len(lesson.steps) - 1))
        self._active_lesson = lesson
        self._replaying = bool(entry.get("completed"))
        self._session = LessonSession(lesson, start)
        self._stack.setCurrentWidget(self._detail_view)
        self._render_step()

    def _back_to_grid(self):
        self._save_progress()
        self._session = None
        self._active_lesson = None
        self._replaying = False
        self._stack.setCurrentWidget(self._grid_view)
        self._refresh_cards()
        self._refresh_header_progress()

    def _step_text(self, step):
        return t(step.text_key, self._language, **step.text_params)

    def _render_step(self, animate=False):
        session = self._session
        if session is None:
            return
        step = session.current
        lesson = session.lesson

        self._lesson_title.setText(t(lesson.title_key, self._language))
        self._lesson_subtitle.setText(t(lesson.subtitle_key, self._language))
        self._step_label.setText(
            t(
                "learn_step",
                self._language,
                current=session.index + 1,
                total=session.total_steps,
            )
        )
        self._step_progress.setRange(0, session.total_steps)
        self._step_progress.setValue(session.completed_steps)

        interactive = step.kind == MOVE and not session.solved
        self._board.set_interactive(interactive, chess.WHITE)
        self._board.set_start_fen(step.fen)
        self._board.set_moves(session.display_moves, animate=animate)
        self._board.clear_hint()
        marks = () if session.solved else step.marks
        arrows = step.arrows if step.kind == INFO else ()
        self._board.set_lesson_marks(marks, arrows)

        self._instruction.setText(self._step_text(step))
        if session.solved:
            self._set_feedback(t(step.success_key, self._language), "success")
        else:
            self._set_feedback("", "")
        self._update_buttons()

    def _render_complete(self):
        session = self._session
        if session is None:
            return
        session.completed = True
        lesson = session.lesson
        self._lesson_title.setText(t(lesson.title_key, self._language))
        self._lesson_subtitle.setText(t(lesson.subtitle_key, self._language))
        self._step_label.setText(
            t(
                "learn_step",
                self._language,
                current=session.total_steps,
                total=session.total_steps,
            )
        )
        self._step_progress.setRange(0, session.total_steps)
        self._step_progress.setValue(session.total_steps)
        self._instruction.setText(t("learn_lesson_complete", self._language))
        self._set_feedback(
            t(
                "learn_complete_detail",
                self._language,
                title=t(lesson.title_key, self._language),
            ),
            "success",
        )
        self._board.set_interactive(False, chess.WHITE)
        self._board.clear_hint()
        self._board.set_lesson_marks((), ())
        self._btn_primary.setText(t("learn_back_short", self._language))
        self._btn_primary.setVisible(True)
        self._btn_hint.setVisible(False)
        self._btn_retry.setVisible(False)
        self._save_progress()

    def _update_buttons(self):
        session = self._session
        if session is None:
            return
        step = session.current
        if step.kind == INFO or session.solved:
            self._btn_primary.setVisible(True)
            last = session.index + 1 >= session.total_steps
            key = "learn_finish" if last else "learn_continue"
            self._btn_primary.setText(t(key, self._language))
        else:
            self._btn_primary.setVisible(False)
        can_hint = step.kind == MOVE and not session.solved and bool(step.hint)
        self._btn_hint.setVisible(can_hint)
        self._btn_retry.setVisible(step.kind == MOVE and not session.solved)

    def _set_feedback(self, text, state=""):
        self._feedback_state = state
        self._feedback.setText(text)
        self._feedback.setProperty("state", state)
        self._feedback.style().unpolish(self._feedback)
        self._feedback.style().polish(self._feedback)

    def _on_move_requested(self, from_square, to_square):
        session = self._session
        if session is None or session.solved:
            self._board.clear_selection()
            return
        step = session.current
        if step.kind != MOVE:
            self._board.clear_selection()
            return

        move = chess.Move(from_square, to_square)
        piece = session.board.piece_at(from_square)
        if (
            piece is not None
            and piece.piece_type == chess.PAWN
            and chess.square_rank(to_square) in (0, 7)
        ):
            promotion = self._board.promotion_choice(to_square, piece.color)
            if promotion is None:
                self._board.clear_selection()
                return
            move = chess.Move(from_square, to_square, promotion=promotion)

        status = session.play(move)
        self._board.clear_selection()
        if status in ("correct", "solved"):
            self._save_progress()
            self._render_step(animate=True)
        elif status == "wrong":
            self._set_feedback(t("learn_wrong", self._language), "error")
        else:
            self._set_feedback("", "")

    def _on_primary(self):
        session = self._session
        if session is None:
            return
        if session.completed:
            self._back_to_grid()
            return
        if session.current.kind != INFO and not session.solved:
            return
        if session.advance():
            self._save_progress()
            if session.completed:
                self._render_complete()
            else:
                self._render_step()

    def _on_hint(self):
        session = self._session
        if session is None or session.solved:
            return
        hint = session.current.hint
        if not hint:
            return
        self._board.set_hint(hint)
        self._set_feedback(t("learn_hint_shown", self._language), "")

    def _on_retry(self):
        session = self._session
        if session is None or session.solved:
            return
        session.retry()
        self._board.clear_hint()
        self._set_feedback("", "")
        self._render_step()

    def _save_progress(self):
        session = self._session
        if session is None or self._active_lesson is None or self._replaying:
            return
        lesson = self._active_lesson
        last_solved = session.solved and session.index + 1 >= session.total_steps
        completed = session.completed or last_solved
        step = session.total_steps if completed else session.completed_steps
        save_lesson_progress(
            lesson.id,
            step,
            session.total_steps,
            completed=completed,
            base_dir=self._progress_base_dir,
        )
        self._progress = load_progress(self._progress_base_dir)
        self._refresh_cards()
        self._refresh_header_progress()

    def _refresh_cards(self):
        for lesson_id, card in self._cards.items():
            card.set_status(self._progress.get(lesson_id))

    def _refresh_header_progress(self):
        if not hasattr(self, "_header_progress"):
            return
        done = sum(1 for entry in self._progress.values() if entry.get("completed"))
        self._header_progress.setText(
            t(
                "learn_progress",
                self._language,
                done=done,
                total=len(self._lessons),
            )
        )
