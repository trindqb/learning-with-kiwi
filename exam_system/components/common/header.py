"""Header với user info"""
import streamlit as st

class UserHeader:
    @staticmethod
    def render(user):
        st.write(f"**{user['full_name']}**")
        # TODO: Add header logic
