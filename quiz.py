
    # Current question
    index = st.session_state.quiz_question_index
    question_number = index + 1

    question = st.session_state.quiz_questions[index]
    question_id = question["id"]

    # Live timer
    show_live_timer()

    # =====================================
    # PROGRESS
    # =====================================

    answered = len(st.session_state.quiz_answers)

    st.write(
        f"Question {question_number} of {TOTAL_QUESTIONS}"
    )

    st.progress(
        answered / TOTAL_QUESTIONS
    )

    st.caption(
        f"{answered} of {TOTAL_QUESTIONS} questions answered"
    )

    # =====================================
    # QUESTION CARD
    # =====================================

    show_question_card(
        question,
        question_number
    )

    # =====================================
    # FOUR BUTTONS IN ONE ROW
    # Previous | VERO | FALSO | Next
    # =====================================

    selected = st.session_state.quiz_answers.get(question_id)

    with st.container(key="quiz_controls_row"):
        previous_col, vero_col, falso_col, next_col = st.columns(
            [1.15, 1, 1, 1.15], gap="small"
        )

        with previous_col:
            with st.container(key="quiz_previous"):
                if st.button(
                    "← Prev",
                    key="quiz_previous_button",
                    disabled=index == 0,
                    use_container_width=True,
                ):
                    go_to_question(index - 1)

        with vero_col:
            with st.container(key="quiz_vero"):
                label = "✓ VERO" if selected is True else "VERO"
                if st.button(
                    label,
                    key=f"vero_{question_id}",
                    use_container_width=True,
                ):
                    select_answer(question_id, True)

        with falso_col:
            with st.container(key="quiz_falso"):
                label = "✕ FALSO" if selected is False else "FALSO"
                if st.button(
                    label,
                    key=f"falso_{question_id}",
                    use_container_width=True,
                ):
                    select_answer(question_id, False)

        with next_col:
            with st.container(key="quiz_next"):
                if st.button(
                    "Next →",
                    key="quiz_next_button",
                    disabled=index == TOTAL_QUESTIONS - 1,
                    use_container_width=True,
                ):
                    go_to_question(index + 1)

    # Keep the existing 30-question scrollable pagination.
    show_pagination()

    # =====================================
    # SUBMIT QUIZ
    # =====================================

    if answered == TOTAL_QUESTIONS:

        st.success("All 30 questions answered.")

        if st.button(
            "Submit Quiz",
            key="quiz_submit_again",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.quiz_show_completion_dialog = True
            st.rerun()
