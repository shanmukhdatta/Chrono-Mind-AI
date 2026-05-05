import { useCallback } from 'react'
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth'
import { auth, googleProvider } from '../lib/firebase'
import { useAuthStore } from '../store/authStore'

export function useAuth() {
  const { setUser, clearUser, setLoading } = useAuthStore()

  const signIn = useCallback(async () => {
    try {
      setLoading(true)
      const result = await signInWithPopup(auth, googleProvider)
      setUser(result.user)
      return result.user
    } catch (error) {
      console.error('Sign in error:', error)
      setLoading(false)
      throw error
    }
  }, [setUser, setLoading])

  const signOutUser = useCallback(async () => {
    try {
      await signOut(auth)
      clearUser()
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }, [clearUser])

  const initAuth = useCallback(() => {
    return onAuthStateChanged(auth, (user) => {
      if (user) {
        setUser(user)
      } else {
        clearUser()
      }
    })
  }, [setUser, clearUser])

  return { signIn, signOutUser, initAuth }
}
