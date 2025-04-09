import streamlit as st
import sqlite3
import pandas as pd

# 데이터베이스 연결 (하나의 파일로 통합: timetable.db)
conn = sqlite3.connect('timetable.db', check_same_thread=False)
cur = conn.cursor()

# users 테이블 생성
cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
''')

# timetable 테이블 생성
cur.execute('''
    CREATE TABLE IF NOT EXISTS timetable (
        username TEXT,
        day TEXT,
        hour INTEGER,
        activity TEXT,
        PRIMARY KEY (username, day, hour)
    )
''')
conn.commit()

# 세션 초기화
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# 요일, 시간 정의
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOURS = list(range(24))

# 앱 제목
st.title("회원제 시간표 관리 시스템")

# 로그인 or 회원가입 선택
if st.session_state.logged_in_user is None:
    mode = st.radio("모드 선택", ["로그인", "회원가입"])

    # 로그인
    if mode == "로그인":
        st.subheader("로그인")
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")

        if st.button("로그인"):
            cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            result = cur.fetchone()
            if result:
                st.session_state.logged_in_user = username
                st.success(f"{username}님, 로그인 성공!")
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")

    # 회원가입
    elif mode == "회원가입":
        st.subheader("회원가입")
        new_username = st.text_input("새 아이디")
        new_password = st.text_input("새 비밀번호", type="password")

        if st.button("회원가입"):
            cur.execute("SELECT * FROM users WHERE username = ?", (new_username,))
            if cur.fetchone():
                st.warning("이미 존재하는 아이디입니다.")
            else:
                cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, new_password))
                conn.commit()
                st.success("회원가입 완료! 로그인 해주세요.")

# 로그인 후 시간표 기능 제공
else:
    username = st.session_state.logged_in_user
    st.info(f"{username}님이 로그인 중입니다.")

    if st.button("로그아웃"):
        st.session_state.logged_in_user = None
        st.success("로그아웃 되었습니다.")
        st.stop()  # 이후 코드 실행 방지

    st.subheader(f"{username}님의 시간표")

    # 기존 시간표 불러오기
    cur.execute("SELECT day, hour, activity FROM timetable WHERE username = ?", (username,))
    rows = cur.fetchall()

    # 빈 시간표 만들기
    timetable = pd.DataFrame("", index=DAYS, columns=HOURS)

    # 기존 데이터 적용
    for day, hour, activity in rows:
        timetable.loc[day, hour] = activity

    # 편집 가능한 시간표
    edited_table = st.data_editor(timetable, num_rows="fixed", key="editor")
    edited_table.columns = edited_table.columns.astype(int)

    if st.button("시간표 저장"):
        cur.execute("DELETE FROM timetable WHERE username = ?", (username,))
        for day in DAYS:
            for hour in HOURS:
                activity = edited_table.loc[day, hour]
                if activity.strip() != "":
                    cur.execute(
                        "INSERT INTO timetable (username, day, hour, activity) VALUES (?, ?, ?, ?)",
                        (username, day, hour, activity)
                    )
        conn.commit()
        st.success("시간표 저장 완료!")

    # 확인용
    if st.checkbox("현재 시간표 보기"):
        st.dataframe(edited_table)
