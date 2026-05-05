import React, { useState, useRef, useCallback } from 'react'
import { Mic, MicOff, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export function VoiceButton({ onTranscript }) {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const recognitionRef = useRef(null)

  const startListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      toast.error('Voice input not supported in this browser. Try Chrome.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognitionRef.current = recognition

    recognition.onstart = () => setIsListening(true)

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setIsListening(false)
      setIsProcessing(true)
      setTimeout(() => {
        setIsProcessing(false)
        if (transcript?.trim()) {
          onTranscript && onTranscript(transcript.trim())
        }
      }, 300)
    }

    recognition.onerror = (event) => {
      setIsListening(false)
      setIsProcessing(false)
      if (event.error === 'not-allowed') {
        toast.error('Microphone access denied. Allow it in browser settings.')
      } else if (event.error === 'no-speech') {
        toast('No speech detected. Try again.', { icon: '🎤' })
      }
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.start()
  }, [onTranscript])

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }, [])

  const handleClick = () => {
    if (isListening) stopListening()
    else startListening()
  }

  return (
    <button
      onClick={handleClick}
      disabled={isProcessing}
      title={isListening ? 'Stop recording' : 'Voice input'}
      className={`p-3 rounded-xl transition-all ${
        isListening
          ? 'bg-red-500 text-white animate-pulse shadow-lg'
          : isProcessing
          ? 'bg-gray-100 text-dark-muted'
          : 'bg-gray-100 text-dark-muted hover:bg-peach/20 hover:text-peach-dark'
      }`}
    >
      {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> :
       isListening ? <MicOff className="w-5 h-5" /> :
       <Mic className="w-5 h-5" />}
    </button>
  )
}
