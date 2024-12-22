import streamlit as st
import os
import tempfile
from groq import Groq
import pandas as pd
import io

# Page configuration
st.set_page_config(page_title="Audio Transcription App", layout="centered", initial_sidebar_state="expanded")

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

# Process audio file
def process_audio(audio_file):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
        tmp_file.write(audio_file.getvalue())
        temp_path = tmp_file.name

    # Process with Groq
    with open(temp_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(temp_path, file.read()),
            model="whisper-large-v3",
            language="vi",
            response_format="verbose_json",
        )

    # Clean up temp file
    os.unlink(temp_path)
    st.session_state['segments'] = transcription.segments
    return transcription.text


# Main layout
st.markdown("""
  <div style='text-align: center; padding: 20px;'>
    <h1 style='color: #1E88E5; margin-bottom: 10px;'>
      🎤 Audio Transcription Service
    </h1>
    <p style='color: #666; font-size: 18px; font-weight: 300;'>
      Upload your audio files and get accurate transcriptions in minutes
    </p>
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 20px 0;'>
      <p style='color: #424242; margin: 0;'>
        ✨ Supports multiple audio formats • Fast processing • Vietnamese language
      </p>
    </div>
  </div>
""", unsafe_allow_html=True)

# Upload file section
uploaded_file = st.file_uploader(
    label="Upload your audio file:",
    type=['mp3', 'wav', 'm4a', 'ogg', 'aac', 'flac'],
    help="Maximum file size: 20MB"
)

if uploaded_file is not None:
  # Display audio player
  st.subheader("Audio Preview")
  audio_format = uploaded_file.type if uploaded_file.type else 'audio/mp3'
  st.audio(uploaded_file, format=audio_format)

  # Check file size
  if uploaded_file.size > 20 * 1024 * 1024:
    st.error("❌ File size exceeds the 20MB limit. Please upload a smaller file.")
  else:
    # Create a placeholder for the spinner
    spinner_placeholder = st.empty()

    # Center the button using markdown and custom CSS
    st.markdown(
      """
      <style>
      div.stButton > button {
        display: block;
        margin: 0 auto;
      }
      </style>
      """,
      unsafe_allow_html=True
    )

    if st.button("🔄 Process Audio"):
      try:
        # Show spinner
        with spinner_placeholder:
          with st.spinner("⏳ Processing your file. Please wait..."):
            transcript = process_audio(uploaded_file)
            st.session_state['transcript'] = transcript

        # Clear the spinner and show success message
        spinner_placeholder.empty()
        st.success("✅ Processing complete! Transcript is ready.")
      except Exception as e:
        spinner_placeholder.empty()
        st.error(f"❌ An error occurred: {e}")

# Transcript display section
if 'transcript' in st.session_state:
    tab1, tab2 = st.tabs(["Full Transcript", "Segmented Transcript"])

    with tab1:
        st.subheader("📝 Complete Transcript")
        # Make transcript editable and store in session state
        edited_full_transcript = st.text_area(
            "Transcript:",
            value=st.session_state['transcript'],
            height=300,
            key="transcript_display"
        )
        st.session_state['edited_transcript'] = edited_full_transcript

        # Download text button with edited content
        st.download_button(
            label="💾 Download Transcript (TXT)",
            data=st.session_state['edited_transcript'],
            file_name="transcript.txt",
            mime="text/plain"
        )

    with tab2:
        st.subheader("🔍 Segmented Transcript")
        segments = st.session_state.get('segments', [])

        # Initialize edited segments in session state if not exists
        if 'edited_segments' not in st.session_state:
            st.session_state['edited_segments'] = {}

        # Create container with fixed height
        with st.container(height=500):
            segments_data = []
            for segment in segments:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.write(f"{segment['start']:.2f}s - {segment['end']:.2f}s")
                with col2:
                    # Get previously edited text or original text
                    segment_key = f"segment_{segment['start']}"
                    initial_text = st.session_state['edited_segments'].get(
                        segment_key,
                        segment['text']
                    )

                    edited_text = st.text_area(
                        label=f"Transcript segment {segment['start']:.2f}-{segment['end']:.2f}",
                        value=initial_text,
                        key=segment_key,
                        height=max(68, len(initial_text) // 40 * 30),
                        label_visibility="collapsed"
                    )

                    # Store edited text in session state
                    st.session_state['edited_segments'][segment_key] = edited_text

                    segments_data.append({
                        'Time': f"{segment['start']:.2f} - {segment['end']:.2f}",
                        'Content': edited_text
                    })

        # Export button outside container with edited content
        if segments_data:
            df = pd.DataFrame(segments_data)
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_data = excel_buffer.getvalue()

            st.download_button(
                label="📊 Download Segments (Excel)",
                data=excel_data,
                file_name="transcript_segments.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Footer
st.markdown("---")
st.markdown("""
  <div style='text-align: center; color: #666; padding: 20px;'>
    <p>
      <span style='font-size: 14px;'>Powered by</span><br>
      <a href='https://streamlit.io' target='_blank' style='text-decoration: none; color: #ff4b4b;'>Streamlit</a> •
      <a href='https://groq.com' target='_blank' style='text-decoration: none; color: #00acee;'>Groq AI</a>
    </p>
    <p style='font-size: 12px; margin-top: 10px;'>
      Developed by <strong>Thuận Nguyễn</strong> | © 2024
    </p>
  </div>
""", unsafe_allow_html=True)
