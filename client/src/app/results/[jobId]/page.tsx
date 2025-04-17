"use client";

import React, { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { JobResult } from "@/components/job-result";
import { useJob } from "@/lib/job-context";

export default function JobResultsPage() {
  const router = useRouter();
  const params = useParams();
  const { fetchJobById, job, jobStatus, loading, error, clearJob } = useJob();

  // Get the job ID from the route parameters
  const jobId = params.jobId as string;

  // Handle page reset/return to home
  const handleReset = () => {
    clearJob();
    router.push("/");
  };

  // Fetch job data when the page loads
  useEffect(() => {
    if (jobId && (!job || job.job_id !== jobId)) {
      console.log("Fetching job with ID:", jobId);
      fetchJobById(jobId);
    }
  }, [jobId, job, fetchJobById]);

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

      {/* Results */}
      <main className="container mx-auto flex-1 py-8 px-4 flex flex-col items-center">
        <JobResult onReset={handleReset} />
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
