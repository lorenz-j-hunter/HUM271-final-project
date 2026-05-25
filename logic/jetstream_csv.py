from flask import render_template
import csv

def get_jetstream_csv(db):
  return render_template('bluesky.html')