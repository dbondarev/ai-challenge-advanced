# -*- coding: utf-8 -*-
"""Shared prompts for day 9 distillation."""

STUDENT_SYS = (
    "How does the last IN message change the prospect's status in this LinkedIn "
    "sales thread? Reply with one word: no_change, rejection, not_ta, positive, "
    "mql, sql, meeting_held."
)

TEACHER_SYS = """You label how the last IN message changes a LinkedIn prospect status.
Reply with one word only: no_change, rejection, not_ta, positive, mql, sql, meeting_held.

Meanings:
- no_change: small talk, already shared, their own pitch to us, or a step the thread already reached
- rejection: the right person refuses our offer, no buying reason
- not_ta: wrong person, left the company, not their area, or points to a colleague
- positive: polite reply or maybe later without a next step; greetings and yes-send-it without a contact
- mql: asks for materials, shares their own email, asks for OUR email or phone, agrees to meet later without an exact time
- sql: shares their own phone, or locks an exact date and time
- meeting_held: the meeting already happened

Own email vs a colleague's: the name inside the address matches the person it belongs to.
greta@example.com from Greta is own email (mql). The same address from someone else is a referral (not_ta).
"""
