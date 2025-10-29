import streamlit as st
import soundfile as sf
import tempfile
import os
import time
from datetime import datetime
from kokoro_onnx import Kokoro
import zipfile
import io

# Page configuration
st.set_page_config(
    page_title="Kokoro Voice Generator",
    page_icon="🎙️",
    layout="wide"
)

# Initialize session state
if 'kokoro' not in st.session_state:
    with st.spinner("Loading Kokoro model..."):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        model_path = os.path.join(base_dir, "model", "kokoro-v1.0.onnx")
        voices_path = os.path.join(base_dir, "model", "voices-v1.0.bin")
        st.session_state.kokoro = Kokoro(model_path, voices_path)

if 'audio_history' not in st.session_state:
    st.session_state.audio_history = []

if 'presets' not in st.session_state:
    st.session_state.presets = {}

# Kokoro-82M voice lists by language (per VOICES.md)
VOICES_BY_LANGUAGE = {
        # American English: 11F 9M
        "English (US)": {
            "lang_code": "en-us",
            "voices": [
                "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica", "af_kore",
                "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
                "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael",
                "am_onyx", "am_puck", "am_santa"
            ],
        },
        # British English: 4F 4M
        "English (UK)": {
            "lang_code": "en-gb",
            "voices": [
                "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
                "bm_daniel", "bm_fable", "bm_george", "bm_lewis"
            ],
        },
        # Japanese: 4F 1M
        "Japanese": {
            "lang_code": "ja",
            "voices": [
                "jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo"
            ],
        },
        # Mandarin Chinese: 4F 4M
        "Chinese (Mandarin)": {
            "lang_code": "zh",
            "voices": [
                "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi",
                "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"
            ],
        },
        # Spanish: 1F 2M
        "Spanish": {
            "lang_code": "es",
            "voices": ["ef_dora", "em_alex", "em_santa"],
        },
        # French: 1F
        "French": {
            "lang_code": "fr",
            "voices": ["ff_siwis"],
        },
        # Hindi: 2F 2M
        "Hindi": {
            "lang_code": "hi",
            "voices": ["hf_alpha", "hf_beta", "hm_omega", "hm_psi"],
        },
        # Italian: 1F 1M
        "Italian": {
            "lang_code": "it",
            "voices": ["if_sara", "im_nicola"],
        },
        # Brazilian Portuguese: 1F 2M
        "Portuguese (BR)": {
            "lang_code": "pt",
            "voices": ["pf_dora", "pm_alex", "pm_santa"],
        },
}

# Text templates
TEXT_TEMPLATES = {
    "Greeting": "Hello! Welcome to Kokoro Voice Generator.",
    "Introduction": "My name is Kokoro, and I'm an AI voice generator powered by advanced text-to-speech technology.",
    "Story": "Once upon a time, in a world where technology and creativity merged, there was a voice generator that could bring any text to life.",
    "News": "Breaking news: Scientists have made remarkable progress in text-to-speech technology, achieving natural-sounding human voices.",
    "Marketing": "Discover the future of voice synthesis. Create professional audio content with ease using our cutting-edge technology.",
    "Educational": "Today we'll learn about the fascinating world of speech synthesis and how artificial intelligence can recreate human voices.",
}

# Title and description
st.title("🎙️ Kokoro Voice Generator")
st.markdown("Generate high-quality speech from text using Kokoro ONNX")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Mode selection
    mode = st.radio(
        "Mode",
        ["Single", "Batch", "Preview"],
        help="Single: Generate one audio. Batch: Generate multiple. Preview: Quick voice test."
    )
    
    # Language selection
    language_names = list(VOICES_BY_LANGUAGE.keys())
    selected_language = st.selectbox(
        "Language",
        options=language_names,
        index=0,
        help="Select the language to filter the available Kokoro-82M voices"
    )
    
    current_lang_code = VOICES_BY_LANGUAGE[selected_language]["lang_code"]
    current_voice_options = VOICES_BY_LANGUAGE[selected_language]["voices"]
    
    # Voice selection with gender indicator
    selected_voice = st.selectbox(
        "Voice",
        options=current_voice_options,
        index=0,
        help="Select a Kokoro-82M voice (from VOICES.md)"
    )
    
    # Show voice info
    gender_emoji = "🚺" if selected_voice.startswith(("af_", "bf_", "jf_", "zf_", "ef_", "ff_", "hf_", "if_", "pf_")) else "🚹"
    st.caption(f"Voice: {gender_emoji} {selected_voice}")
    
    # Speed control
    speed = st.slider(
        "Speed",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="Speech speed multiplier"
    )
    
    st.markdown("---")
    
    # Presets section
    st.subheader("💾 Presets")
    preset_name = st.text_input("Save preset as:", placeholder="e.g., 'Narrator'")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", use_container_width=True):
            if preset_name:
                st.session_state.presets[preset_name] = {
                    "language": selected_language,
                    "voice": selected_voice,
                    "speed": speed
                }
                st.success(f"Preset '{preset_name}' saved!")
            else:
                st.warning("Enter a preset name")
    
    with col2:
        if st.button("Delete", use_container_width=True):
            if preset_name and preset_name in st.session_state.presets:
                del st.session_state.presets[preset_name]
                st.success(f"Preset '{preset_name}' deleted!")
    
    if st.session_state.presets:
        selected_preset = st.selectbox("Load preset:", options=list(st.session_state.presets.keys()))
        if st.button("Load", use_container_width=True):
            preset = st.session_state.presets[selected_preset]
            st.session_state.preset_loaded = preset
            st.rerun()
    
    if 'preset_loaded' in st.session_state:
        preset = st.session_state.preset_loaded
        selected_language = preset["language"]
        selected_voice = preset["voice"]
        speed = preset["speed"]
        del st.session_state.preset_loaded

# Main content area
tab1, tab2, tab3 = st.tabs(["📝 Generate", "📚 Templates", "📜 History"])

with tab1:
    if mode == "Single":
        st.header("📝 Text Input")
        
        # Text templates quick access
        template_col1, template_col2 = st.columns(2)
        with template_col1:
            selected_template = st.selectbox("Load template:", [None] + list(TEXT_TEMPLATES.keys()))
            if selected_template:
                text_input = st.text_area(
                    "Enter your text here",
                    height=150,
                    value=TEXT_TEMPLATES[selected_template],
                    placeholder="Type or paste the text you want to convert to speech...",
                    help="Enter the text you want to convert to speech"
                )
            else:
                text_input = st.text_area(
                    "Enter your text here",
                    height=150,
                    placeholder="Type or paste the text you want to convert to speech...",
                    help="Enter the text you want to convert to speech"
                )
        
        # Spacer and Generate button directly under the text box
        st.write("")
        generate_button = st.button("🎵 Generate Audio", type="primary")

        # Text statistics below the button
        if text_input:
            char_count = len(text_input)
            word_count = len(text_input.split())
            # Rough estimate: ~150 words per minute for average speech
            estimated_duration = (word_count / 150) * 60 / speed if word_count > 0 else 0
            
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.metric("Characters", char_count)
            with stat_col2:
                st.metric("Words", word_count)
            with stat_col3:
                st.metric("Est. Duration", f"{estimated_duration:.1f}s")
        
        # Audio output section
        if generate_button:
            if not text_input.strip():
                st.warning("⚠️ Please enter some text to generate audio.")
            else:
                try:
                    start_time = time.time()
                    with st.spinner("Generating audio... This may take a moment."):
                        # Generate audio
                        samples, sample_rate = st.session_state.kokoro.create(
                            text_input,
                            voice=selected_voice,
                            speed=speed,
                            lang=current_lang_code
                        )
                        
                        generation_time = time.time() - start_time
                        duration = len(samples) / sample_rate
                        
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                            sf.write(tmp_file.name, samples, sample_rate)
                            tmp_file_path = tmp_file.name
                        
                        # Save to history
                        audio_data = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "text": text_input[:100] + "..." if len(text_input) > 100 else text_input,
                            "voice": selected_voice,
                            "language": selected_language,
                            "speed": speed,
                            "duration": duration,
                            "file_path": tmp_file_path,
                            "samples": samples,
                            "sample_rate": sample_rate
                        }
                        st.session_state.audio_history.insert(0, audio_data)
                        
                        # Display audio player
                        st.success("✅ Audio generated successfully!")
                        st.audio(tmp_file_path, format="audio/wav")
                        
                        # Download buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            with open(tmp_file_path, "rb") as audio_file:
                                audio_bytes = audio_file.read()
                                st.download_button(
                                    label="⬇️ Download WAV",
                                    data=audio_bytes,
                                    file_name=f"kokoro_{selected_voice}_{int(time.time())}.wav",
                                    mime="audio/wav",
                                    use_container_width=True
                                )
                        
                        # Display info
                        info_col1, info_col2, info_col3 = st.columns(3)
                        with info_col1:
                            st.info(f"📊 Sample Rate: {sample_rate} Hz")
                        with info_col2:
                            st.info(f"⏱️ Duration: {duration:.2f}s")
                        with info_col3:
                            st.info(f"⚡ Generated in: {generation_time:.2f}s")
                        
                except Exception as e:
                    st.error(f"❌ Error generating audio: {str(e)}")
                    st.exception(e)
    
    elif mode == "Batch":
        st.header("📦 Batch Processing")
        st.markdown("Generate multiple audio files at once. Enter one text per line.")
        
        batch_text = st.text_area(
            "Enter texts (one per line)",
            height=200,
            placeholder="Text 1\nText 2\nText 3\n...",
            help="Enter multiple texts, one per line"
        )
        
        if st.button("🎵 Generate All", type="primary"):
            if not batch_text.strip():
                st.warning("⚠️ Please enter some texts to generate audio.")
            else:
                texts = [line.strip() for line in batch_text.split('\n') if line.strip()]
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                audio_files = []
                errors = []
                
                for i, text in enumerate(texts):
                    status_text.text(f"Processing {i+1}/{len(texts)}: {text[:50]}...")
                    progress_bar.progress((i + 1) / len(texts))
                    
                    try:
                        samples, sample_rate = st.session_state.kokoro.create(
                            text,
                            voice=selected_voice,
                            speed=speed,
                            lang=current_lang_code
                        )
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                            sf.write(tmp_file.name, samples, sample_rate)
                            audio_files.append({
                                "text": text[:50],
                                "file": tmp_file.name,
                                "name": f"batch_{i+1}_{selected_voice}_{int(time.time())}.wav"
                            })
                    except Exception as e:
                        errors.append(f"Text {i+1}: {str(e)}")
                
                status_text.empty()
                progress_bar.empty()
                
                if audio_files:
                    st.success(f"✅ Generated {len(audio_files)} audio file(s)!")
                    
                    # Individual downloads
                    for audio_file in audio_files:
                        with open(audio_file["file"], "rb") as f:
                            st.download_button(
                                label=f"⬇️ Download: {audio_file['text']}...",
                                data=f.read(),
                                file_name=audio_file["name"],
                                mime="audio/wav"
                            )
                    
                    # Batch download as ZIP
                    if len(audio_files) > 1:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for audio_file in audio_files:
                                zip_file.write(audio_file["file"], audio_file["name"])
                                os.unlink(audio_file["file"])
                        
                        st.download_button(
                            label="📦 Download All as ZIP",
                            data=zip_buffer.getvalue(),
                            file_name=f"kokoro_batch_{int(time.time())}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                
                if errors:
                    st.error("Some errors occurred:")
                    for error in errors:
                        st.error(error)
    
    elif mode == "Preview":
        st.header("🎤 Voice Preview")
        st.markdown("Quick preview of voices with a short test phrase.")
        
        preview_text = st.text_input(
            "Preview text",
            value="Hello! This is a preview of the voice.",
            help="Short text to preview the voice"
        )
        
        if st.button("▶️ Play Preview", type="primary"):
            if not preview_text.strip():
                st.warning("⚠️ Please enter preview text.")
            else:
                try:
                    with st.spinner("Generating preview..."):
                        samples, sample_rate = st.session_state.kokoro.create(
                            preview_text,
                            voice=selected_voice,
                            speed=speed,
                            lang=current_lang_code
                        )
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                            sf.write(tmp_file.name, samples, sample_rate)
                            st.audio(tmp_file.name, format="audio/wav")
                            os.unlink(tmp_file.name)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with tab2:
    st.header("📚 Text Templates")
    st.markdown("Quick access to common text templates for testing voices.")
    
    for name, template in TEXT_TEMPLATES.items():
        with st.expander(f"📄 {name}"):
            st.text(template)
            if st.button(f"Use '{name}' Template", key=f"template_{name}"):
                st.session_state.selected_template = template
                st.info(f"Template '{name}' selected! Switch to Generate tab to see it.")

with tab3:
    st.header("📜 Generation History")
    
    if not st.session_state.audio_history:
        st.info("No generation history yet. Generate some audio to see it here!")
    else:
        # Clear history button
        if st.button("🗑️ Clear History"):
            # Clean up old files
            for item in st.session_state.audio_history:
                if os.path.exists(item["file_path"]):
                    os.unlink(item["file_path"])
            st.session_state.audio_history = []
            st.rerun()
        
        for idx, item in enumerate(st.session_state.audio_history[:10]):  # Show last 10
            with st.expander(f"🎵 {item['timestamp']} - {item['voice']} ({item['language']})"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.text(f"Text: {item['text']}")
                    st.caption(f"Speed: {item['speed']}x | Duration: {item['duration']:.2f}s")
                    if os.path.exists(item["file_path"]):
                        st.audio(item["file_path"], format="audio/wav")
                        with open(item["file_path"], "rb") as f:
                            st.download_button(
                                label="⬇️ Download",
                                data=f.read(),
                                file_name=f"kokoro_{item['voice']}_{idx}.wav",
                                mime="audio/wav",
                                key=f"hist_dl_{idx}"
                            )
                    else:
                        st.warning("Audio file no longer available")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by [xposed73](https://github.com/xposed73)")


