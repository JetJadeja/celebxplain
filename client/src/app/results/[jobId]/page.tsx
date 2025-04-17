"use client";

import React, { useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { JobResult } from "@/components/job-result";
import { useJob } from "@/lib/job-context";

export default function JobResultsPage() {
  const router = useRouter();
  const params = useParams();
  const { fetchJobById, job, jobStatus, loading, error, clearJob } = useJob();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isUnmountedRef = useRef(false);

  // Get the job ID from the route parameters
  const jobId = params.jobId as string;

  // Function to schedule the next fetch
  const scheduleFetch = () => {
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    // Schedule next fetch in 5 seconds if job is still active
    console.log("Checking status");
    if (
      !isUnmountedRef.current &&
      (!jobStatus ||
        (jobStatus.status !== "completed" &&
          jobStatus.status !== "failed" &&
          jobStatus.status !== "error"))
    ) {
      timeoutRef.current = setTimeout(() => {
        if (!isUnmountedRef.current && jobId) {
          fetchJobById(jobId)
            .then(() => {
              // Schedule next fetch
              scheduleFetch();
            })
            .catch((err) => {
              console.error("Fetch error:", err);
              // Still schedule next fetch on error
              scheduleFetch();
            });
        }
      }, 5000);
    }
  };

  // Handle page reset/return to home
  const handleReset = () => {
    clearJob();
    router.push("/");
  };

  // Setup initial fetch and cleanup
  useEffect(() => {
    isUnmountedRef.current = false;

    // Initial fetch
    if (jobId) {
      fetchJobById(jobId)
        .then(() => {
          scheduleFetch();
        })
        .catch((err) => {
          console.error("Initial fetch error:", err);
          scheduleFetch();
        });
    }

    // Cleanup on unmount
    return () => {
      isUnmountedRef.current = true;

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [jobId, fetchJobById]);

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
