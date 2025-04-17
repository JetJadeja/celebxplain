"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CelebrityGrid } from "@/components/celebrity-grid";
import { ProcessSteps } from "@/components/process-steps";
import { useJob } from "@/lib/job-context";
import { Celebrity } from "@/lib/api";

export default function Home() {
  const [selectedCelebrity, setSelectedCelebrity] = useState<Celebrity | null>(
    null
  );
  const [topic, setTopic] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { clearJob, createNewJob } = useJob();
  const router = useRouter();

  const handleGenerate = async () => {
    if (!selectedCelebrity || !topic || isSubmitting) return;

    // Set submitting state to prevent multiple submissions
    setIsSubmitting(true);

    try {
      // Clear any existing job first
      clearJob();

      // Create the job and get the job ID
      const newJob = await createNewJob(topic, selectedCelebrity.id);

      // Navigate to the results page with the job ID in the path
      router.push(`/results/${newJob.job_id}`);
    } catch (error) {
      console.error("Error creating job:", error);
      setIsSubmitting(false);
    }
  };

  // Process steps with icons
  const steps = [
    {
      title: "Select a celebrity & topic",
      description: "Choose who you want to explain your topic",
      icon: "1",
    },
    {
      title: "AI generates the explanation",
      description: "Our AI creates a personalized script",
      icon: "2",
    },
    {
      title: "Watch your video",
      description: "Enjoy your custom explanation",
      icon: "3",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-primary/10 flex flex-col">
      {/* Header */}
      <header className="container mx-auto py-8">
        <div className="flex flex-col items-center text-center space-y-4">
          <h1 className="heading-lg max-w-2xl">
            Celebrity Explainer Generator
          </h1>
          <p className="tagline max-w-xl">
            Learn anything, explained by your favorite celebrities
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto flex-1 py-8 px-4 flex flex-col items-center">
        <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Celebrity Selection */}
          <div className="flex flex-col space-y-4">
            <h2 className="heading-md mb-2">Choose a Celebrity</h2>
            <CelebrityGrid
              onSelect={setSelectedCelebrity}
              selectedId={selectedCelebrity?.id}
            />
          </div>

          {/* Topic Input */}
          <div className="flex flex-col space-y-4">
            <h2 className="heading-md mb-2">What would you like explained?</h2>
            <div className="bg-card p-6 rounded-lg shadow-sm">
              <Input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter any topic or question..."
                className="mb-4"
              />
              <Button
                variant="gradient"
                size="lg"
                className="w-full"
                onClick={handleGenerate}
                disabled={!selectedCelebrity || !topic || isSubmitting}
              >
                {isSubmitting ? "Creating..." : "Generate Explanation"}
              </Button>

              {/* Selected summary */}
              {selectedCelebrity && (
                <div className="mt-4 p-3 bg-primary/10 rounded-md">
                  <p className="text-sm">
                    <span className="font-medium">
                      {selectedCelebrity.name}
                    </span>{" "}
                    will explain{" "}
                    <span className="font-medium">{topic || "your topic"}</span>
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Process Visualization */}
        <div className="w-full py-8">
          <h2 className="heading-md text-center mb-8">How It Works</h2>
          <ProcessSteps steps={steps} />
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto py-6 border-t border-border">
        <div className="flex justify-center items-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} Celebrity Explainer Generator</p>
        </div>
      </footer>
    </div>
  );
}
