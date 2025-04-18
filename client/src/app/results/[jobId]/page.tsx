"use client";

import React, { useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { JobResult } from "@/components/job-result";
import { useJob } from "@/lib/job-context";
import {
  Window,
  WindowHeader,
  WindowContent,
  Button,
  Frame,
  Hourglass,
} from "react95";

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

  // Determine if the job is actively processing
  const isProcessing =
    jobStatus &&
    jobStatus.status !== "completed" &&
    jobStatus.status !== "failed" &&
    jobStatus.status !== "error";

  return (
    <div
      className="min-h-screen p-4 flex flex-col items-center justify-center"
      style={{ background: "teal" }}
    >
      {/* Optional: Add a frame around the entire window area if desired */}
      {/* <Frame variant="outside" className="w-full max-w-5xl p-1"> */}
      <Window className="w-full max-w-4xl mx-auto">
        <WindowHeader className="flex items-center justify-between">
          <span>Celebrity Explainer Generator</span>
          <Button onClick={() => router.push("/")} size="sm">
            <span style={{ transform: "translateY(-1px)" }}>X</span>
          </Button>
        </WindowHeader>
        <WindowContent className="flex flex-col items-center">
          {/* Tagline moved to top */}
          <p className="tagline mb-4">
            Learn anything, explained by your favorite celebrities
          </p>

          {/* Conditionally show Hourglass and updated message */}
          {isProcessing && (
            <div className="flex flex-col items-center mb-4">
              <Hourglass size={32} className="mb-2" />
              <p className="text-center text-sm">
                Your explanation is being generated.
                <br />
                This can take up to 15 minutes.
              </p>
            </div>
          )}

          {/* Frame around the JobResult */}
          <Frame variant="inside" className="w-full p-4 shadow-inner">
            <main className="flex-1 flex flex-col items-center">
              <JobResult onReset={handleReset} />
            </main>
          </Frame>

          {/* Footer inside WindowContent */}
          <footer className="mt-6 text-center text-xs">
            <p>© {new Date().getFullYear()} Celebrity Explainer Generator</p>
          </footer>
        </WindowContent>
      </Window>
      {/* </Frame> */}
    </div>
  );
}
