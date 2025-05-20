"use client";

import React, { useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { JobResult } from "@/components/job-result";
import { useJob } from "@/lib/job-context";
// import {
//   Window,
//   WindowHeader,
//   WindowContent,
//   Button,
//   Frame,
//   Hourglass,
// } from "react95"; // Remove React95 imports

// Shadcn UI and Lucide Icons
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { X, Timer } from "lucide-react"; // Added X and Timer for processing

export default function JobResultsPage() {
  const router = useRouter();
  const params = useParams();
  // Use jobData from the context
  const { fetchJobById, jobData, loading, error, clearJob } = useJob();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isUnmountedRef = useRef(false);

  const jobId = params.jobId as string;

  const scheduleFetch = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    // Check status from jobData.job.status
    if (
      !isUnmountedRef.current &&
      jobId &&
      (!jobData?.job?.status ||
        (jobData.job.status !== "completed" &&
          jobData.job.status !== "failed" &&
          jobData.job.status !== "error"))
    ) {
      timeoutRef.current = setTimeout(() => {
        if (!isUnmountedRef.current && jobId) {
          fetchJobById(jobId)
            .then(() => {
              scheduleFetch(); // Reschedule after successful fetch
            })
            .catch((err) => {
              console.error("Polling fetch error:", err);
              scheduleFetch(); // Still attempt to reschedule on error
            });
        }
      }, 5000);
    }
  };

  const handleReset = () => {
    clearJob();
    router.push("/");
  };

  useEffect(() => {
    isUnmountedRef.current = false;
    if (jobId) {
      // Clear any existing job data for this new ID if it differs from current jobData
      if (jobData && jobData.job.job_id !== jobId) {
        clearJob();
      }
      fetchJobById(jobId)
        .then(() => {
          scheduleFetch();
        })
        .catch((err) => {
          console.error("Initial fetch error for job:", jobId, err);
          scheduleFetch(); // Attempt to reschedule even if initial fetch fails
        });
    }
    return () => {
      isUnmountedRef.current = true;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]); // Dependencies: only jobId. fetchJobById and clearJob are stable from context.

  // Determine if the job is actively processing based on jobData
  const isProcessing =
    !error && // Not in an error state
    jobData?.job?.status && // jobData and status exist
    jobData.job.status !== "completed" &&
    jobData.job.status !== "failed" &&
    jobData.job.status !== "error";

  return (
    <div className="min-h-screen bg-slate-900 text-slate-50 p-4 sm:p-6 lg:p-8 flex flex-col items-center justify-center">
      <Card className="w-full max-w-3xl shadow-xl bg-slate-800/70 backdrop-blur-md border-slate-700">
        <CardHeader className="flex flex-row items-center justify-between pb-4 pt-6 px-6">
          <CardTitle className="text-2xl font-semibold text-slate-100">
            Explanation Progress
          </CardTitle>
          <Button
            onClick={() => router.push("/")}
            variant="ghost"
            size="icon"
            className="text-slate-400 hover:text-slate-100 hover:bg-slate-700"
          >
            <X size={20} />
            <span className="sr-only">Close</span>
          </Button>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          {/* Show processing indicator if loading initially OR if status is processing */}
          {(loading && !jobData) || (isProcessing && !error) ? (
            <div className="flex flex-col items-center justify-center text-center p-6 rounded-lg">
              <Timer size={40} className="text-primary mb-3 animate-pulse" />
              <h3 className="text-xl font-semibold text-slate-200 mb-1">
                Your explanation is cooking!
              </h3>
              <p className="text-slate-400 text-sm max-w-md">
                This can sometimes take a few moments, especially for complex
                topics. We're working on it and will update you here.
              </p>
            </div>
          ) : null}

          {/* JobResult component will now use jobData from context to display details, video, or errors */}
          {/* It should not show its own loading/error if the main page already handles it, unless JobResult has specific sub-loading states */}
          <JobResult onReset={handleReset} />
        </CardContent>
        <CardFooter className="px-6 py-4 border-t border-slate-700 text-center">
          <p className="text-xs text-slate-500">
            &copy; {new Date().getFullYear()} Celebrity Explainer. Results for
            Job ID: {jobId}
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
