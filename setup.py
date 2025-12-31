#!/usr/bin/env python3
import os
import sys

def setup_database():
    """إعداد قاعدة البيانات"""
    from database import db
    print("✅ قاعدة البيانات جاهزة")

if __name__ == "__main__":
    setup_database()
