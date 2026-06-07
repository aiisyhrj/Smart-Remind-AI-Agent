"""
SmartRemind — Assignment Reminder AI Agent
Built with Reflex (pure Python, no JavaScript, no API key needed)
Matches system diagram: 6 layers — Input, Processing, Priority Engine,
Reminder Generation, Dashboard/Visualization, Feedback Loop
Updated for Reflex v0.9.4+ Compatibility
"""

import reflex as rx
from datetime import date, datetime
from typing import List
from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────────────────────
class Assignment(BaseModel):
    id: int
    name: str
    subject: str
    due_date: str
    days_remaining: int = 0
    priority: str = "upcoming"
    reminder: str = ""
    done: bool = False


# ─────────────────────────────────────────────────────────────
# LAYER 2 — Assignment Processing (date calc)
# ─────────────────────────────────────────────────────────────
def calc_days(due_date_str: str) -> int:
    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        return (due - date.today()).days
    except Exception:
        return 999


# ─────────────────────────────────────────────────────────────
# LAYER 3 — Priority & Urgency Engine
# ─────────────────────────────────────────────────────────────
def calc_priority(days: int) -> str:
    if days < 0:   return "overdue"
    if days == 0:  return "due_today"
    if days == 1:  return "due_tomorrow"
    return "upcoming"


# ─────────────────────────────────────────────────────────────
# LAYER 4 — Reminder Generation Layer
# ─────────────────────────────────────────────────────────────
def generate_reminder(name: str, subject: str, days: int, priority: str) -> str:
    if priority == "overdue":
        return f"⚠️ OVERDUE by {abs(days)} day(s)! Submit '{name}' immediately and contact your lecturer."
    if priority == "due_today":
        return f"🚨 '{name}' ({subject}) is due TODAY! Stop everything and finish it now."
    if priority == "due_tomorrow":
        return f"🔴 '{name}' ({subject}) is due TOMORROW. Finish it tonight — no more delays!"
    if days <= 3:
        return f"🟠 '{name}' ({subject}) is due in {days} days. Start now to avoid last-minute panic."
    if days <= 7:
        return f"🟡 '{name}' ({subject}) is due in {days} days. Make a plan and start drafting."
    return f"🟢 '{name}' ({subject}) is due in {days} days. You have time — don't forget it!"


# ─────────────────────────────────────────────────────────────
# STATE — manages all layers
# ─────────────────────────────────────────────────────────────
class State(rx.State):
    # Assignment store
    assignments: List[Assignment] = [
        Assignment(id=1, name="AI Agent Report",       subject="Artificial Intelligence", due_date=date.today().strftime("%Y-%m-%d")),
        Assignment(id=2, name="Data Structures Quiz",  subject="Computer Science",        due_date=date.today().replace(day=date.today().day + 2).strftime("%Y-%m-%d")),
        Assignment(id=3, name="Network Security Essay", subject="Cybersecurity",          due_date=date.today().replace(day=date.today().day + 7).strftime("%Y-%m-%d")),
    ]
    next_id: int = 4

    # Form fields
    inp_name: str = ""
    inp_subject: str = ""
    inp_due: str = date.today().strftime("%Y-%m-%d")

    # Filter / sort controls (Layer 5)
    filter_subject: str = "All"
    sort_by: str = "due_date"

    # UI state
    show_reminder_panel: bool = False

    # EXPLICIT SETTERS (Fixes the v0.9.4+ AttributeError)
    def change_inp_name(self, val: str):
        self.inp_name = val

    def change_inp_subject(self, val: str):
        self.inp_subject = val

    def change_inp_due(self, val: str):
        self.inp_due = val

    def _process_assignment(self, a: Assignment) -> Assignment:
        """Run assignment through layers 2, 3, 4."""
        days     = calc_days(a.due_date)
        priority = calc_priority(days)
        reminder = generate_reminder(a.name, a.subject, days, priority)
        return Assignment(
            id=a.id, name=a.name, subject=a.subject,
            due_date=a.due_date, days_remaining=days,
            priority=priority, reminder=reminder, done=a.done,
        )

    def _refresh(self):
        self.assignments = [self._process_assignment(a) for a in self.assignments]

    def on_load(self):
        self._refresh()

    # ── LAYER 1: User Input ──
    def add_assignment(self):
        if not self.inp_name.strip() or not self.inp_subject.strip() or not self.inp_due:
            return
        new_a = Assignment(
            id=self.next_id, name=self.inp_name.strip(),
            subject=self.inp_subject.strip(), due_date=self.inp_due,
        )
        self.assignments.append(self._process_assignment(new_a))
        self.next_id += 1
        self.inp_name = ""
        self.inp_subject = ""
        self.show_reminder_panel = True

    # ── LAYER 6: Feedback Loop ──
    def delete_assignment(self, aid: int):
        self.assignments = [a for a in self.assignments if a.id != aid]

    def mark_done(self, aid: int):
        for i, a in enumerate(self.assignments):
            if a.id == aid:
                self.assignments[i] = Assignment(
                    id=a.id, name=a.name, subject=a.subject,
                    due_date=a.due_date, days_remaining=a.days_remaining,
                    priority=a.priority, reminder=a.reminder, done=not a.done,
                )

    def set_filter(self, val: str):
        self.filter_subject = val

    def set_sort(self, val: str):
        self.sort_by = val

    def toggle_reminder_panel(self):
        self.show_reminder_panel = not self.show_reminder_panel

    # ── Computed values ──
    @rx.var
    def subjects(self) -> List[str]:
        s = list({a.subject for a in self.assignments})
        return ["All"] + sorted(s)

    @rx.var
    def filtered_sorted(self) -> List[Assignment]:
        items = [a for a in self.assignments if not a.done]
        if self.filter_subject != "All":
            items = [a for a in items if a.subject == self.filter_subject]
        if self.sort_by == "due_date":
            items = sorted(items, key=lambda a: a.days_remaining)
        elif self.sort_by == "priority":
            order = {"overdue": 0, "due_today": 1, "due_tomorrow": 2, "upcoming": 3}
            items = sorted(items, key=lambda a: order.get(a.priority, 4))
        return items

    @rx.var
    def done_items(self) -> List[Assignment]:
        return [a for a in self.assignments if a.done]

    @rx.var
    def total_count(self) -> int:
        return len(self.assignments)

    @rx.var
    def overdue_count(self) -> int:
        return len([a for a in self.assignments if a.priority == "overdue" and not a.done])

    @rx.var
    def upcoming_count(self) -> int:
        return len([a for a in self.assignments if a.priority == "upcoming" and not a.done])

    #@rx.var
    #def urgent_reminders(self) -> List[str]:
       ## urgent = [a for a in self.assignments if a.priority in ("overdue","due_today","due_tomorrow") and not a.done]
       # urgent.sort(key=lambda a: a.days_remaining)
       # return [a.reminder for a in urgent]
    @rx.var
    def urgent_reminders(self) -> List[str]:
        # 🟢 New version: Pulls ALL active assignments regardless of priority
        items = [a for a in self.assignments if not a.done]
        # Sort them so the most urgent ones still appear at the very top
        items.sort(key=lambda a: a.days_remaining)
        return [a.reminder for a in items]

# ─────────────────────────────────────────────────────────────
# COLOURS & HELPERS
# ─────────────────────────────────────────────────────────────
BLUE  = "#1F4E79"
MID   = "#2E75B6"
LIGHT = "#D6E4F0"
BG    = "#F5F7FA"
WHITE = "#FFFFFF"


def priority_badge(priority: str) -> rx.Component:
    return rx.cond(
        priority == "overdue",
        rx.badge("OVERDUE",      color_scheme="red",    radius="full", size="1"),
        rx.cond(
            priority == "due_today",
            rx.badge("Due Today",   color_scheme="red",    radius="full", size="1"),
            rx.cond(
                priority == "due_tomorrow",
                rx.badge("Due Tomorrow", color_scheme="orange", radius="full", size="1"),
                rx.badge("Upcoming",     color_scheme="green",  radius="full", size="1"),
            )
        )
    )


def days_label(a: Assignment) -> rx.Component:
    return rx.cond(
        a.days_remaining < 0,
        rx.text(f"{abs(a.days_remaining)}d overdue", size="1", color="red"),
        rx.cond(
            a.days_remaining == 0,
            rx.text("Today!", size="1", weight="bold", color="red"),
            rx.text(f"{a.days_remaining} days left", size="1", color="gray"),
        )
    )


# ─────────────────────────────────────────────────────────────
# COMPONENTS
# ─────────────────────────────────────────────────────────────

def stat_card(label: str, value, color: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(value, size="7", weight="bold", color=color),
            rx.text(label, size="1", color="gray"),
            align="center", spacing="1",
        ),
        background=WHITE, border=f"1px solid #E5E7EB",
        border_radius="10px", padding="16px 20px",
        flex="1", text_align="center",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


def assignment_card(a: Assignment) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("book-open", size=14, color=MID),
                    rx.text(a.name, weight="bold", size="3", color ="#1F4E79"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.icon("graduation-cap", size=12, color="gray"),
                    rx.text(a.subject, size="2", color="gray"),
                    rx.text("·", color="gray"),
                    rx.icon("calendar", size=12, color="gray"),
                    rx.text(a.due_date, size="2", color="gray"),
                    spacing="1", align="center",
                ),
                spacing="1", align_items="start", flex="1",
            ),
            rx.vstack(
                priority_badge(a.priority),
                days_label(a),
                spacing="1", align="end",
            ),
            rx.vstack(
                rx.icon_button(
                    rx.icon("check", size=13),
                    on_click=State.mark_done(a.id),
                    size="1", variant="soft", color_scheme="green",
                    title="Mark as done",
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=13),
                    on_click=State.delete_assignment(a.id),
                    size="1", variant="soft", color_scheme="red",
                    title="Delete",
                ),
                spacing="1",
            ),
            align="center", spacing="3", width="100%",
        ),
        background=WHITE,
        border="1px solid #E5E7EB",
        border_left=rx.cond(
            a.priority == "overdue",      "4px solid #EF4444",
            rx.cond(
                a.priority == "due_today",    "4px solid #EF4444",
                rx.cond(
                    a.priority == "due_tomorrow", "4px solid #F97316",
                    "4px solid #22C55E",
                )
            )
        ),
        border_radius="8px",
        padding="12px 14px",
        width="100%",
        box_shadow="0 1px 2px rgba(0,0,0,0.04)",
    )


def reminder_card(text: str) -> rx.Component:
    return rx.box(
        rx.text(text, size="2", line_height="1.7", color="#0A0101"),
        background=LIGHT, border="1px solid #A8C8E8",
        border_radius="8px", padding="10px 14px",
        width="100%",
    )


def section_header(num: str, title: str, color: str) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(num, color=WHITE, weight="bold", size="2"),
            background=color, border_radius="full",
            width="26px", height="26px",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.text(title, weight="bold", size="3", color=color),
        spacing="2", align="center", margin_bottom="12px",
    )


def completed_assignment_item(a: Assignment) -> rx.Component:
    """Extracted layout wrapper function ensuring v0.9.4 foreach compatibility"""
    return rx.hstack(
        rx.icon("check-circle", size=14, color="green"),
        rx.text(a.name, size="2", color="gray", text_decoration="line-through"),
        rx.text(a.subject, size="1", color="gray"),
        rx.spacer(),
        rx.icon_button(
            rx.icon("rotate-ccw", size=12),
            on_click=State.mark_done(a.id),
            size="1", variant="ghost", color_scheme="gray",
            title="Undo",
        ),
        rx.icon_button(
            rx.icon("trash-2", size=12),
            on_click=State.delete_assignment(a.id),
            size="1", variant="ghost", color_scheme="red",
        ),
        width="100%", align="center",
    )


# ─────────────────────────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────────────────────────
def index() -> rx.Component:
    return rx.box(
        rx.vstack(

            # ── TOP HEADER ──
            rx.vstack(
                rx.heading("SmartRemind", size="8", color=BLUE, weight="bold"),
                rx.text("Assignment Reminder AI Agent", color=MID, size="3"),
                rx.badge("OBSERVE → THINK → ACT", color_scheme="blue", radius="full", size="1"),
                align="center", spacing="1", margin_bottom="24px",
            ),

            # ── LAYER 5: ANALYTICS SUMMARY ──
            rx.box(
                section_header("", "Dashboard & Analytics", "#7C3AED"),
                rx.hstack(
                    stat_card("Total Assignments", State.total_count,   BLUE),
                    stat_card("Overdue",           State.overdue_count, "#DC2626"),
                    stat_card("Upcoming",          State.upcoming_count,"#16A34A"),
                    spacing="3", width="100%",
                ),
                background=WHITE, border="1px solid #E5E7EB",
                border_radius="12px", padding="16px",
                width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
            ),

            # ── LAYER 1: USER INPUT ──
            rx.box(
                section_header("", "New Assignment", MID),
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Assignment Name", size="1", color="gray", weight="medium"),
                            rx.input(
                                placeholder="e.g. Lab Report",
                                value=State.inp_name,
                                on_change=State.change_inp_name,  # Updated setter
                                width="100%",
                            ),
                            spacing="1", width="100%",
                        ),
                        rx.vstack(
                            rx.text("Subject", size="1", color="gray", weight="medium"),
                            rx.input(
                                placeholder="e.g. Biology",
                                value=State.inp_subject,
                                on_change=State.change_inp_subject,  # Updated setter
                                width="100%",
                            ),
                            spacing="1", width="100%",
                        ),
                        rx.vstack(
                            rx.text("Due Date", size="1", color="gray", weight="medium"),
                            rx.input(
                                type="date",
                                value=State.inp_due,
                                on_change=State.change_inp_due,  # Updated setter
                                width="100%",
                            ),
                            spacing="1", width="100%",
                        ),
                        spacing="3", width="100%",
                        flex_wrap="wrap",
                    ),
                    rx.button(
                        rx.icon("plus", size=14), "Add Assignment",
                        on_click=State.add_assignment,
                        background=MID, color=WHITE,
                        border_radius="8px", width="100%",
                        _hover={"background": BLUE},
                    ),
                    spacing="3", width="100%",
                ),
                background=WHITE, border="1px solid #E5E7EB",
                border_radius="12px", padding="16px",
                width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
            ),

            # ── LAYER 5 CONTROLS: Filter + Sort ──
            rx.box(
                rx.hstack(
                    rx.hstack(
                        rx.icon("filter", size=14, color=MID),
                        rx.text("Filter by subject:", size="2", color="gray"),
                        rx.select(
                            State.subjects,
                            value=State.filter_subject,
                            on_change=State.set_filter,
                            size="1",
                        ),
                        spacing="2", align="center",
                    ),
                    rx.hstack(
                        rx.icon("arrow-up-down", size=14, color=MID),
                        rx.text("Sort by:", size="2", color="gray"),
                        rx.select(
                            ["due_date", "priority"],
                            value=State.sort_by,
                            on_change=State.set_sort,
                            size="1",
                        ),
                        spacing="2", align="center",
                    ),
                    spacing="6", flex_wrap="wrap",
                ),
                background=WHITE, border="1px solid #E5E7EB",
                border_radius="12px", padding="12px 16px",
                width="100%",
            ),

            # ── LAYERS 2/3/4: Assignment cards ──
            rx.box(
                section_header("", "To-Do List", "#EA580C"),
                rx.text(
                    "Agent automatically calculates days remaining (Layer 2), classifies urgency (Layer 3), and generates reminders (Layer 4).",
                    size="1", color="gray", margin_bottom="12px",
                ),
                rx.cond(
                    State.filtered_sorted,  # Boolean context array check (v0.9.x standard)
                    rx.vstack(
                        rx.foreach(State.filtered_sorted, assignment_card),
                        spacing="2", width="100%",
                    ),
                    rx.box(
                        rx.text("No active assignments. Add one above!", color="gray", size="2"),
                        text_align="center", padding="24px",
                    ),
                ),
                background=WHITE, border="1px solid #E5E7EB",
                border_radius="12px", padding="16px",
                width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
            ),

            # ── LAYER 4: Reminder Panel ──
            rx.box(
                rx.hstack(
                    section_header("", "AI Agent Generated Reminders", "#590468"),
                    rx.button(
                        rx.icon("bell", size=13), "Generate Reminders",
                        on_click=State.toggle_reminder_panel,
                        size="1", color_scheme="red", variant="soft",
                    ),
                    justify="between", align="center", width="100%",
                    margin_bottom="0px",
                ),
                rx.cond(
                    State.show_reminder_panel,
                    rx.vstack(
                        rx.cond(
                            State.urgent_reminders,
                            rx.vstack(
                                rx.foreach(State.urgent_reminders, reminder_card),
                                spacing="2", width="100%", margin_top="12px",
                            ),
                            rx.text("✅ No urgent items right now — great job staying on top of things!", size="2", color="green"),
                        ),
                    ),
                ),
                background=WHITE, border="1px solid #E5E7EB",
                border_radius="12px", padding="16px",
                width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
            ),

            # ── LAYER 6: Feedback Loop — Done items ──
            rx.cond(
                State.done_items,
                rx.box(
                    section_header("", "Completed Assignments", "#16A34A"),
                    rx.vstack(
                        rx.foreach(
                            State.done_items,
                            completed_assignment_item  # Safely separated loop component
                        ),
                        spacing="2", width="100%",
                    ),
                    background=WHITE, border="1px solid #E5E7EB",
                    border_radius="12px", padding="16px",
                    width="100%",
                ),
            ),

            rx.text(
                "SmartRemind · AI Agents Course Milestone 2 · Built with Reflex (pure Python)",
                size="1", color="gray", text_align="center", margin_top="8px",
            ),

            spacing="4", width="100%", max_width="760px",
            margin="0 auto", padding="24px 16px 48px",
        ),
        background=BG, min_height="100vh",
    )


# ─────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────
app = rx.App(
    theme=rx.theme(appearance="light", accent_color="blue"),
)
app.add_page(index, on_load=State.on_load)