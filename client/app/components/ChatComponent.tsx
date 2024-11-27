'use client'

import { FormEvent, useState, useRef, useEffect} from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Bot, User, Send } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function ChatComponent() {

  const [messages, setMessages] = useState<Message[]>([{ role: 'assistant', content: 'Hello! I am a helpful assistant designed to help you with your construction needs. What questions do you have?'},])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [threadId, setThreadId] = useState('')
  const messageEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth'})

  }, [messages])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()  
    if (input.trim() === '') return

    const userMessage: Message = {role: 'user', content: input}
    setMessages(prevMessages => [...prevMessages, userMessage])
    setInput('')

    setIsLoading(true)
    try {
      // If it is the first user question
      let endpoint = ""
      if (messages.length < 2) {
        endpoint = `${process.env.NEXT_PUBLIC_API_URL}/api/fairfax-construction-assistant/`
      }
      else {
        endpoint = `${process.env.NEXT_PUBLIC_API_URL}/api/fairfax-construction-assistant/${threadId}`
      }
      console.log(endpoint)
      console.log(input)
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }) // Is input not ''?
      })
      
      if (!response.ok) {
        throw new Error("Failed to get response from the API")
      }
      
      const data = await response.json()
      const aiMessage: Message = { role: 'assistant', content: data.answer }
      setThreadId(data.thread_id)
      setMessages(prevMessages => [...prevMessages, aiMessage])
    } catch (error) {
      console.error('Error:', error)
      setMessages(prevMessages => [...prevMessages, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.'}])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-5xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">Fairfax Construction Assistant</CardTitle>
      </CardHeader>
      {/* Chat Messages */}
      <CardContent className="flex-grow overflow-hidden">
        <ScrollArea className="h-full pr-4 font-mono">
          {messages.map((msg, index) => (
            <div key={index} className={`flex mb-4 ${msg.role === 'user' ? 'justify-end': 'justify-start'}`}>
              <div className={`flex items-start max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse': ''}`}>
                <div className={`flex items-center justify-center w-8 h-8 rounded-full ${msg.role === 'user' ? 'bg-blue-500 ml-2': 'bg-gray-300 mr-2'}`}>
                  {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-gray-600"/>}
                </div>
                  <pre className={`p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-black'} whitespace-pre-wrap break-words`}>
                    <code>{msg.content}</code>
                  </pre>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="flex items-start max-w-[80%]">
                <div className={"flex items-center justify-center w-8 h-8 rounded-full bg-gray-300 mr-2"}>
                  <Bot className="w-5 h-5 text-gray-600"/>
                </div>
                <pre className="p-3 rounded-lg bg-gray-100 text-black whitespace-pre-wrap break-words">
                  AI is thinking...
                </pre>
              </div>
            </div>
          )}
          <div ref={messageEndRef}/>
        </ScrollArea>
      </CardContent>
      {/* Chat Input */}
      <CardFooter>
        <form onSubmit={handleSubmit} className="flex space-x-2 w-full">
          <Input 
            className="flex-grow"
            type="text"
            placeholder="Type your message here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <Button type="submit" disabled={isLoading}>
            <Send className="w-4 h-4, mr-2"/>
            Send
          </Button>
        </form>
      </CardFooter>
    </Card>
  )
}