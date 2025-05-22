"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Brain, Zap, User, Wand2, Film } from "lucide-react"; // Added User, Wand2, Film
import PhotoCarousel from "@/components/ui/photo-carousel"; // Import the carousel

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {/* Header */}
      <header className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Brain className="h-8 w-8 text-purple-400" />
          <h1 className="text-2xl font-bold tracking-tight">Spew</h1>
        </div>
        <nav className="space-x-4">
          <Link href="/dashboard">
            <Button className="bg-purple-600 hover:bg-purple-700 text-white">
              Dashboard <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-center text-center py-16 sm:py-24">
        <div className="max-w-3xl">
          <div className="inline-flex items-center justify-center bg-purple-500/20 text-purple-300 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <Zap className="h-4 w-4 mr-2" />
            Unlock a Ridiculously Fun Way of Learning
          </div>
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight mb-6">
            The Most Absurd Way to <br />
            <span className="bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 text-transparent bg-clip-text">
              Actually Learn Stuff
            </span>
          </h2>
          <p className="text-lg sm:text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            Ever wished learning complex topics was as entertaining as watching
            your favorite celebrity? Now it can be. Spew uses AI to generate
            unique video explanations in the style of well-known personalities.
          </p>
          <div className="flex flex-col sm:flex-row justify-center items-center gap-4">
            <Link href="/dashboard">
              <Button
                size="lg"
                className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-lg py-3 px-8 rounded-lg shadow-lg transform transition-all duration-300 hover:scale-105"
              >
                Start Creating Now <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button
              size="lg"
              variant="outline"
              className="w-full sm:w-auto bg-transparent text-white border-purple-500 hover:bg-purple-500/20 hover:text-purple-300 text-lg py-3 px-8 rounded-lg shadow-lg"
              onClick={() => {
                const featuresSection = document.getElementById("features");
                if (featuresSection) {
                  featuresSection.scrollIntoView({ behavior: "smooth" });
                }
              }}
            >
              Learn More
            </Button>
          </div>
        </div>
      </main>

      {/* Photo Carousel Section */}
      <PhotoCarousel />

      {/* Features Section */}
      <section id="features" className="py-16 sm:py-24 bg-slate-900/50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
              Why You'll Love Spew
            </h3>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              Discover the features that make learning engaging and fun.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-slate-800/70 p-6 rounded-lg shadow-xl border border-purple-500/30 hover:shadow-purple-500/20 transition-shadow duration-300">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-gradient-to-r from-purple-600 to-pink-600 text-white mb-4">
                <User className="h-6 w-6" />
              </div>
              <h4 className="text-xl font-semibold mb-2 text-slate-100">
                Personalized Explanations
              </h4>
              <p className="text-slate-400">
                Choose from a list of celebrities. Our AI crafts a script in
                their unique style.
              </p>
            </div>
            <div className="bg-slate-800/70 p-6 rounded-lg shadow-xl border border-purple-500/30 hover:shadow-purple-500/20 transition-shadow duration-300">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-gradient-to-r from-purple-600 to-pink-600 text-white mb-4">
                <Wand2 className="h-6 w-6" />
              </div>
              <h4 className="text-xl font-semibold mb-2 text-slate-100">
                AI-Powered Content
              </h4>
              <p className="text-slate-400">
                Leveraging cutting-edge AI to generate engaging and accurate
                video scripts for any topic.
              </p>
            </div>
            <div className="bg-slate-800/70 p-6 rounded-lg shadow-xl border border-purple-500/30 hover:shadow-purple-500/20 transition-shadow duration-300">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-gradient-to-r from-purple-600 to-pink-600 text-white mb-4">
                <Film className="h-6 w-6" />
              </div>
              <h4 className="text-xl font-semibold mb-2 text-slate-100">
                Instant Video Generation
              </h4>
              <p className="text-slate-400">
                Go from idea to a unique, celebrity-narrated video in minutes.
                Learning has never been faster or more fun.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works (Simplified) */}
      <section className="py-16 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
              Simple Steps to Genius
            </h3>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              Creating your personalized explainer video is easy.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div className="flex flex-col items-center">
              <div className="flex items-center justify-center h-16 w-16 rounded-full bg-purple-500/20 text-purple-300 border-2 border-purple-400 mb-4">
                <span className="text-2xl font-bold">1</span>
              </div>
              <h4 className="text-xl font-semibold mb-2 text-slate-100">
                Pick a Celebrity
              </h4>
              <p className="text-slate-400 px-4">
                Select who you want to hear from.
              </p>
            </div>
            <div className="flex flex-col items-center">
              <div className="flex items-center justify-center h-16 w-16 rounded-full bg-purple-500/20 text-purple-300 border-2 border-purple-400 mb-4">
                <span className="text-2xl font-bold">2</span>
              </div>
              <h4 className="text-xl font-semibold mb-2 text-slate-100">
                Enter Your Topic
              </h4>
              <p className="text-slate-400 px-4">
                Tell us what you want to learn about.
              </p>
            </div>
            <div className="flex flex-col items-center">
              <div className="flex items-center justify-center h-16 w-16 rounded-full bg-purple-500/20 text-purple-300 border-2 border-purple-400 mb-4">
                <span className="text-2xl font-bold">3</span>
              </div>
              <h4 className="text-xl font-semibold mb-2 text-slate-100">
                Generate & Watch
              </h4>
              <p className="text-slate-400 px-4">
                AI crafts your video. Enjoy!
              </p>
            </div>
          </div>
          <div className="text-center mt-12">
            <Link href="/dashboard">
              <Button
                size="lg"
                className="bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white text-lg py-3 px-8 rounded-lg shadow-lg transform transition-all duration-300 hover:scale-105"
              >
                Try It Free <Zap className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-slate-900/70 border-t border-slate-700/50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-400">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Brain className="h-6 w-6 text-purple-400" />
            <h1 className="text-xl font-bold">Spew</h1>
          </div>
          <p className="text-sm">
            &copy; {new Date().getFullYear()} Spew. All rights reserved.
            Transforming education, one celebrity at a time.
          </p>
        </div>
      </footer>
    </div>
  );
}
