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
import { X, Timer, Loader2 } from "lucide-react"; // Added X and Timer, Loader2 for processing

export default function JobResultsPage() {
  const router = useRouter();
  const params = useParams();
  const { fetchJobById, job, jobStatus, loading, error, clearJob } = useJob(); // loading and error are available
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isUnmountedRef = useRef(false);

  const jobId = params.jobId as string;

  const scheduleFetch = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (
      !isUnmountedRef.current &&
      jobId && // Ensure jobId is present
      (!jobStatus ||
        (jobStatus.status !== "completed" &&
          jobStatus.status !== "failed" &&
          jobStatus.status !== "error"))
    ) {
      timeoutRef.current = setTimeout(() => {
        if (!isUnmountedRef.current && jobId) {
          fetchJobById(jobId)
            .then(() => {
              scheduleFetch();
            })
            .catch((err) => {
              console.error("Polling fetch error:", err); // Differentiate from initial fetch error
              scheduleFetch(); // Still attempt to reschedule
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
      // Clear any existing job data for this new ID if it differs from current job
      if (job && job.job_id !== jobId) {
        clearJob();
      }
      fetchJobById(jobId)
        .then(() => {
          scheduleFetch();
        })
        .catch((err) => {
          console.error("Initial fetch error for job:", jobId, err);
          // Potentially set an error state here to be displayed by JobResult
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
  }, [jobId]); // Removed fetchJobById and clearJob from deps as they should be stable

  const isProcessing =
    jobStatus &&
    jobStatus.status !== "completed" &&
    jobStatus.status !== "failed" &&
    jobStatus.status !== "error";

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
          {isProcessing && !error && (
            <div className="flex flex-col items-center justify-center text-center p-6 bg-slate-700/50 rounded-lg border border-slate-600">
              <Timer size={40} className="text-primary mb-3 animate-pulse" />
              <h3 className="text-xl font-semibold text-slate-200 mb-1">
                Your explanation is cooking!
              </h3>
              <p className="text-slate-400 text-sm max-w-md">
                This can sometimes take a few moments, especially for complex
                topics. We're working on it and will update you here.
              </p>
            </div>
          )}

          {/* JobResult component will handle its own loading/error/success states based on useJob context */}
          <div className="bg-slate-800 p-0 sm:p-0 rounded-lg_NO_NEED_FOR_THIS_JobResult_is_a_Card_Now">
            <JobResult onReset={handleReset} />
          </div>
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
