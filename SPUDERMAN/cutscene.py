"""MP4 cutscene playback for Spuderman.

Pygame has no native video support, so frames are decoded with OpenCV and the
audio track is pulled out once with ffmpeg (bundled by imageio-ffmpeg) and
handed to pygame.mixer.music. Playback is driven off the audio clock so the
picture never drifts away from the sound.

Requires:  pip install opencv-python imageio-ffmpeg
If either package is missing the cutscene is skipped instead of crashing the
game.
"""

import subprocess
import sys
from os import makedirs
from os.path import join, dirname, abspath, basename, splitext, isfile

import pygame

BASE_DIR  = dirname(abspath(__file__))
CACHE_DIR = join(BASE_DIR, "audio", "_cutscene_cache")

SKIP_KEYS = (pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER)

_HINT_TEXT       = "SPACE  /  ESC   —   skip"
_HINT_DELAY_MS   = 1500   # how long before the skip hint fades in
_HINT_FADE_MS    = 600
_END_FADE_MS     = 400


# ---------------------------------------------------------------------------
# Audio track extraction (cached on first play)
# ---------------------------------------------------------------------------

def _extract_audio(video_path):
    """Return a path to a WAV of the video's audio track, or None."""
    wav_path = join(CACHE_DIR, splitext(basename(video_path))[0] + ".wav")
    if isfile(wav_path):
        return wav_path

    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

    makedirs(CACHE_DIR, exist_ok=True)
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", video_path,
           "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", wav_path]

    # CREATE_NO_WINDOW keeps a console from flashing up on Windows
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.run(cmd, check=True, creationflags=flags,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return None

    return wav_path if isfile(wav_path) else None


def _start_audio(video_path):
    """Begin playing the video's audio. Returns True if sound is running."""
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except pygame.error:
            return False

    wav_path = _extract_audio(video_path)
    if not wav_path:
        return False

    try:
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()
    except pygame.error:
        return False
    return True


# ---------------------------------------------------------------------------
# Frame helpers
# ---------------------------------------------------------------------------

def _fit_rect(src_w, src_h, dst_w, dst_h):
    """Aspect-preserving fit — returns (width, height, x, y) with letterboxing."""
    scale = min(dst_w / src_w, dst_h / src_h)
    w, h  = int(src_w * scale), int(src_h * scale)
    return w, h, (dst_w - w) // 2, (dst_h - h) // 2


def _to_surface(frame, cv2):
    """Convert an OpenCV BGR frame into a pygame Surface."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    return pygame.image.frombuffer(rgb.tobytes(), (w, h), "RGB")


def _draw_skip_hint(screen, font, elapsed_ms):
    if elapsed_ms < _HINT_DELAY_MS:
        return
    fade  = min(1.0, (elapsed_ms - _HINT_DELAY_MS) / _HINT_FADE_MS)
    label = font.render(_HINT_TEXT, True, (200, 210, 235))
    label.set_alpha(int(150 * fade))
    rect = label.get_rect(bottomright=(screen.get_width() - 28,
                                       screen.get_height() - 22))
    shadow = font.render(_HINT_TEXT, True, (0, 0, 0))
    shadow.set_alpha(int(150 * fade))
    screen.blit(shadow, rect.move(2, 2))
    screen.blit(label, rect)


def _fade_to_black(screen, clock, last_surface, duration_ms):
    if last_surface is None:
        return
    start = pygame.time.get_ticks()
    veil  = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    while True:
        elapsed = pygame.time.get_ticks() - start
        if elapsed >= duration_ms:
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill((0, 0, 0))
        screen.blit(last_surface[0], last_surface[1])
        veil.fill((0, 0, 0, int(255 * elapsed / duration_ms)))
        screen.blit(veil, (0, 0))
        pygame.display.flip()
        clock.tick(60)
    screen.fill((0, 0, 0))
    pygame.display.flip()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def play_video(screen, clock, video_path, allow_skip=True):
    """Play an mp4 full-screen inside the existing pygame window.

    Returns True once the video has finished (or was skipped), False if it
    could not be played at all so the caller can just carry on.
    """
    if not isfile(video_path):
        print(f"[cutscene] missing video: {video_path}")
        return False

    try:
        import cv2
    except ImportError:
        print("[cutscene] opencv-python not installed — skipping cutscene. "
              "Install with:  pip install opencv-python imageio-ffmpeg")
        return False

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[cutscene] could not open: {video_path}")
        return False

    fps         = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total       = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    src_w       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scr_w,scr_h = screen.get_size()

    fit_w, fit_h, off_x, off_y = _fit_rect(src_w, src_h, scr_w, scr_h)
    needs_scale = (fit_w, fit_h) != (src_w, src_h)

    hint_font  = pygame.font.SysFont(None, 26)
    has_audio  = _start_audio(video_path)
    start_ms   = pygame.time.get_ticks()

    screen.fill((0, 0, 0))
    pygame.display.flip()

    decoded_idx = -1          # index of the last frame pulled off the decoder
    current     = None        # (surface, topleft) currently on screen
    skipped     = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.mixer.music.stop()
                pygame.quit()
                sys.exit()
            if allow_skip and (
                    (event.type == pygame.KEYDOWN and event.key in SKIP_KEYS) or
                    (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)):
                skipped = True

        if skipped:
            break

        # The audio clock is authoritative when we have it; get_pos() returns
        # -1 once the track has finished playing.
        if has_audio:
            pos = pygame.mixer.music.get_pos()
            elapsed_ms = pos if pos >= 0 else pygame.time.get_ticks() - start_ms
        else:
            elapsed_ms = pygame.time.get_ticks() - start_ms

        target_idx = int(elapsed_ms / 1000.0 * fps)
        if total and target_idx >= total:
            break

        # Catch up to the target frame, dropping any we fell behind on.
        eof = False
        while decoded_idx < target_idx:
            ok, frame = cap.read()
            if not ok:
                eof = True
                break
            decoded_idx += 1
            if decoded_idx == target_idx:
                surf = _to_surface(frame, cv2)
                if needs_scale:
                    surf = pygame.transform.smoothscale(surf, (fit_w, fit_h))
                current = (surf, (off_x, off_y))
        if eof:
            break

        if current is not None:
            screen.fill((0, 0, 0))
            screen.blit(current[0], current[1])
            if allow_skip:
                _draw_skip_hint(screen, hint_font, elapsed_ms)
            pygame.display.flip()

        clock.tick(60)

    cap.release()
    if has_audio:
        if skipped:
            pygame.mixer.music.stop()
        else:
            pygame.mixer.music.fadeout(_END_FADE_MS)

    if skipped:
        screen.fill((0, 0, 0))
        pygame.display.flip()
    else:
        _fade_to_black(screen, clock, current, _END_FADE_MS)

    pygame.event.clear()
    return True
