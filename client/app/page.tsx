import { ChatComponent } from './components/ChatComponent'

export default function Home() {
  return (
    <main className="flex min-h-screen flex_col items-center justify-center p-4 bg-gradient-to-b from-blue-100 to-white">
      <ChatComponent/>
    </main>
  )
}