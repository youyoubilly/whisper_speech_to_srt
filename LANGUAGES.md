# Language Support

The Whisper large-v3 model supports transcription in 99+ languages. You can specify the language to improve transcription speed and accuracy.

## Usage

```bash
# Specify English
python whisper_speech_to_srt.py audio.mp3 --language en

# Short form
python whisper_speech_to_srt.py audio.mp3 --lang en

# Auto-detect (default)
python whisper_speech_to_srt.py audio.mp3
```

## Benefits of Specifying Language

- **Faster transcription** - Skips language detection step
- **Better accuracy** - Optimized for the target language
- **Improved dialect handling** - Better results with accents

## Supported Languages

### Major Languages
- `en` - English
- `zh` - Chinese (Mandarin)
- `yue` - Cantonese
- `es` - Spanish
- `fr` - French
- `de` - German
- `ja` - Japanese
- `ko` - Korean
- `ru` - Russian
- `ar` - Arabic
- `pt` - Portuguese
- `it` - Italian
- `hi` - Hindi
- `tr` - Turkish

### European Languages
- `nl` - Dutch
- `pl` - Polish
- `sv` - Swedish
- `da` - Danish
- `no` - Norwegian
- `fi` - Finnish
- `cs` - Czech
- `el` - Greek
- `ro` - Romanian
- `hu` - Hungarian
- `uk` - Ukrainian
- `bg` - Bulgarian
- `hr` - Croatian
- `sr` - Serbian
- `sk` - Slovak
- `sl` - Slovenian
- `lt` - Lithuanian
- `lv` - Latvian
- `et` - Estonian
- `is` - Icelandic
- `ca` - Catalan
- `eu` - Basque
- `cy` - Welsh
- `ga` - Irish
- `mt` - Maltese

### Asian Languages
- `th` - Thai
- `vi` - Vietnamese
- `id` - Indonesian
- `ms` - Malay
- `tl` - Tagalog
- `bn` - Bengali
- `ta` - Tamil
- `te` - Telugu
- `kn` - Kannada
- `ml` - Malayalam
- `mr` - Marathi
- `gu` - Gujarati
- `pa` - Punjabi
- `ur` - Urdu
- `ne` - Nepali
- `si` - Sinhala
- `km` - Khmer
- `lo` - Lao
- `my` - Burmese
- `jv` - Javanese
- `su` - Sundanese

### Middle Eastern & Central Asian
- `he` - Hebrew
- `fa` - Persian
- `az` - Azerbaijani
- `hy` - Armenian
- `ka` - Georgian
- `kk` - Kazakh
- `uz` - Uzbek
- `tg` - Tajik
- `tk` - Turkmen
- `ps` - Pashto
- `sd` - Sindhi

### African Languages
- `sw` - Swahili
- `af` - Afrikaans
- `am` - Amharic
- `ha` - Hausa
- `so` - Somali
- `yo` - Yoruba
- `sn` - Shona
- `mg` - Malagasy

### Other Languages
- `bs` - Bosnian
- `sq` - Albanian
- `mk` - Macedonian
- `gl` - Galician
- `be` - Belarusian
- `br` - Breton
- `oc` - Occitan
- `yi` - Yiddish
- `la` - Latin
- `mi` - Maori
- `haw` - Hawaiian
- `ht` - Haitian Creole

## Examples

```bash
# Process English audio with large-v3 model
python whisper_speech_to_srt.py interview.mp3 --large-v3 --language en

# Process Chinese audio to output directory
python whisper_speech_to_srt.py speech.m4a --language zh -o output

# Batch process Spanish files
python whisper_speech_to_srt.py ./audio_folder --language es --recursive

# Auto-detect language (no language flag)
python whisper_speech_to_srt.py unknown.mp3
```

## Performance Notes

**Best Performance (10+ languages):**
- English, Spanish, French, German, Italian, Portuguese, Dutch, Russian, Chinese, Japanese, Korean

**Good Performance:**
- Most European and major Asian languages

**Variable Performance:**
- Languages with limited training data may have lower accuracy
- Performance varies by accent and dialect

## Tips

1. **Known language?** Always specify it for best results
2. **Mixed languages?** Use auto-detect or the primary language
3. **Unclear audio?** Auto-detect might help identify the language first
4. **Accents?** Specifying the language helps handle regional variations

