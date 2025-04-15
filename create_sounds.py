import numpy as np
import os

try:
    from scipy.io import wavfile
    have_scipy = True
except ImportError:
    have_scipy = False

# Create the sounds directory if it doesn't exist
os.makedirs('sounds', exist_ok=True)

if have_scipy:
    # Create a simple drop sound (falling tone)
    sample_rate = 44100
    duration = 0.3
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    drop_note = np.sin(2 * np.pi * 500 * t) * np.exp(-5 * t)
    drop_note = (drop_note * 32767).astype(np.int16)
    wavfile.write('sounds/drop.wav', sample_rate, drop_note)

    # Create a win sound (ascending notes)
    duration = 0.6
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    win_note1 = np.sin(2 * np.pi * 400 * t) * np.exp(-3 * t) * (t < 0.2)
    win_note2 = np.sin(2 * np.pi * 600 * t) * np.exp(-3 * (t-0.2)) * (t >= 0.2) * (t < 0.4)
    win_note3 = np.sin(2 * np.pi * 800 * t) * np.exp(-3 * (t-0.4)) * (t >= 0.4)
    win_sound = win_note1 + win_note2 + win_note3
    win_sound = (win_sound * 32767 / np.max(np.abs(win_sound))).astype(np.int16)
    wavfile.write('sounds/win.wav', sample_rate, win_sound)

    # Create a lose sound (descending notes)
    lose_note1 = np.sin(2 * np.pi * 800 * t) * np.exp(-3 * t) * (t < 0.2)
    lose_note2 = np.sin(2 * np.pi * 600 * t) * np.exp(-3 * (t-0.2)) * (t >= 0.2) * (t < 0.4)
    lose_note3 = np.sin(2 * np.pi * 300 * t) * np.exp(-3 * (t-0.4)) * (t >= 0.4)
    lose_sound = lose_note1 + lose_note2 + lose_note3
    lose_sound = (lose_sound * 32767 / np.max(np.abs(lose_sound))).astype(np.int16)
    wavfile.write('sounds/lose.wav', sample_rate, lose_sound)

    print('Sound files created successfully!')
else:
    print("SciPy not found. Installing simple empty sound files instead.")
    # Create empty sound files as placeholders
    with open('sounds/drop.wav', 'wb') as f:
        f.write(b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
    with open('sounds/win.wav', 'wb') as f:
        f.write(b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
    with open('sounds/lose.wav', 'wb') as f:
        f.write(b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
    print('Empty sound files created as placeholders.') 