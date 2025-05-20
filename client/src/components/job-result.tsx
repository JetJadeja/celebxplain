"use client";

import React from "react";
// import { GroupBox, Button, TextInput, Frame } from "react95"; // Old React95 imports
import { useJob } from "@/lib/job-context";
import { useParams } from "next/navigation";
import {
  Loader,
  FilePlus,
  CheckCircle,
  AlertCircle,
  MessageSquare,
  Clapperboard,
  Video,
} from "lucide-react";

// Shadcn UI Imports
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
  CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface JobResultProps {
  onReset: () => void;
}

// Helper to get status icon
const getStatusIcon = (status?: string) => {
  const lowerStatus = status?.toLowerCase() || "";
  if (lowerStatus.includes("complete"))
    return <CheckCircle size={16} className="mr-2 text-green-500" />;
  if (lowerStatus.includes("fail"))
    return <AlertCircle size={16} className="mr-2 text-red-500" />;
  if (lowerStatus.includes("error"))
    return <AlertCircle size={16} className="mr-2 text-red-500" />;
  if (lowerStatus.includes("processing"))
    return <Loader size={16} className="mr-2 animate-spin" />;
  if (lowerStatus.includes("created"))
    return <FilePlus size={16} className="mr-2 text-blue-500" />;
  if (lowerStatus.includes("generating speech"))
    return <MessageSquare size={16} className="mr-2 text-indigo-500" />;
  if (lowerStatus.includes("generating visuals"))
    return <Clapperboard size={16} className="mr-2 text-purple-500" />;
  // Default or other statuses
  return <Loader size={16} className="mr-2 animate-spin" />;
};

// Helper function to render updates timeline (Enhanced for Shadcn)
const UpdatesTimeline = React.memo(
  ({ updates, title = "Job Updates" }: { updates: any[]; title?: string }) => {
    if (!updates || updates.length === 0) return null;

    return (
      <div className="w-full mt-6">
        <div className="pb-4">
          <h3 className="text-lg text-slate-100 font-semibold">{title}</h3>
        </div>
        <div>
          {updates.length > 0 ? (
            <div className="space-y-1 text-sm">
              {updates.map((update, index) => (
                <div
                  key={update.id || index}
                  className="flex items-start p-3 border-b border-slate-700 last:border-b-0"
                >
                  <div className="flex-shrink-0 mt-1">
                    {getStatusIcon(update.status)}
                  </div>
                  <div className="flex-grow ml-3">
                    <div className="flex justify-between items-center">
                      <span className="font-medium capitalize text-slate-200">
                        {update.status}
                      </span>
                      <span className="text-xs text-slate-400 whitespace-nowrap ml-2">
                        {new Date(update.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </span>
                    </div>
                    {update.message && (
                      <p className="text-xs text-slate-400 mt-0.5">
                        {update.message}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400 text-center p-6">
              No updates yet...
            </p>
          )}
        </div>
      </div>
    );
  }
);
UpdatesTimeline.displayName = "UpdatesTimeline";

// Helper function to display job ID (using Shadcn Input)
const JobIdDisplay = ({ id }: { id?: string }) => {
  if (!id) return null;
  return (
    <div className="flex items-center mt-2">
      <label
        htmlFor="jobIdInput"
        className="text-sm mr-2 whitespace-nowrap font-medium text-slate-200"
      >
        Job ID:
      </label>
      <Input
        id="jobIdInput"
        value={id}
        readOnly
        className="text-sm bg-slate-700 border-slate-600 text-slate-50 placeholder:text-slate-400"
      />
    </div>
  );
};

export function JobResult({ onReset }: JobResultProps) {
  // Consume jobData from the context
  const { jobData, loading, error } = useJob();
  const params = useParams();

  const currentJobId = params.jobId as string;
  const jobDetails = jobData?.job;
  const jobUpdates = jobData?.updates || [];

  // Initial loading state (while jobData is null and not an error)
  if (loading && !jobData && !error) {
    return (
      <div className="w-full max-w-2xl mx-auto py-4">
        <div className="text-center">
          <div className="flex items-center justify-center mb-3">
            <Loader size={24} className="mr-2 animate-spin text-slate-300" />
            <p className="text-slate-400">Retrieving job details...</p>
          </div>
          <JobIdDisplay id={currentJobId} />
        </div>
      </div>
    );
  }

  // Error state from context
  if (error && !jobDetails) {
    // Show context error if no jobDetails to display specific error from
    return (
      <div className="w-full max-w-2xl mx-auto py-4">
        <div className="mb-4">
          <div className="flex items-center text-destructive">
            <AlertCircle size={20} className="mr-2 flex-shrink-0" />
            <h3 className="text-xl font-semibold">Error</h3>
          </div>
          <p className="text-destructive/90 text-sm mt-1">
            We encountered a problem retrieving the job details.
          </p>
        </div>
        <div className="mb-4">
          <p className="text-sm text-destructive/90 mb-3">{error}</p>
          <JobIdDisplay id={currentJobId} />
        </div>
        <div>
          <Button onClick={onReset} variant="outline" className="w-full">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // If jobData is null but not loading and no error, it might mean no job initiated or cleared.
  if (!jobDetails) {
    // This state should ideally be handled by the parent page (e.g., showing "No job selected" or redirecting).
    // For now, a minimal message or null if parent handles it.
    return null; // Or a placeholder like <p>No job data available.</p>
  }

  // Job failed state (from jobDetails.status)
  if (jobDetails.status === "failed" || jobDetails.status === "error") {
    return (
      <div className="w-full max-w-2xl mx-auto py-4">
        <div className="mb-4">
          <div className="flex items-center text-destructive">
            <AlertCircle size={20} className="mr-2 flex-shrink-0" />
            <h3 className="text-xl font-semibold">Generation Failed</h3>
          </div>
          <p className="text-destructive/90 text-sm mt-1">
            We couldn't generate your explanation.
          </p>
        </div>
        <div className="mb-4">
          <p className="text-sm text-destructive/90 mb-1">
            Reason: {jobDetails.error || "Unknown error occurred"}
          </p>
          <JobIdDisplay id={jobDetails.job_id} />
          <UpdatesTimeline updates={jobUpdates} title="Attempt Details" />
        </div>
        <div>
          <Button onClick={onReset} variant="outline" className="w-full mt-4">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // Job completed successfully
  if (jobDetails.status === "completed") {
    const absoluteVideoUrl = jobDetails.video_url
      ? `http://127.0.0.1:8000${jobDetails.video_url}`
      : null;
    return (
      <div className="w-full max-w-2xl mx-auto py-4">
        {/* Video Player is the primary content for completed jobs with video */}
        {jobDetails.video_available && absoluteVideoUrl ? (
          <div className="my-6 rounded-lg overflow-hidden border border-slate-700 shadow-lg">
            <video
              controls
              width="100%"
              src={absoluteVideoUrl}
              className="aspect-video bg-slate-900"
              autoPlay
              playsInline
            >
              Your browser does not support the video tag.
            </video>
          </div>
        ) : (
          // If video not available but job is complete, show a message or just the text.
          <div className="my-6 p-4 h-auto flex flex-col items-center justify-center bg-slate-700/50 border border-dashed border-slate-600 rounded-lg">
            <Video size={40} className="text-slate-400 mb-2" />
            <p className="text-slate-400 text-sm">
              Video is not available for this explanation.
            </p>
          </div>
        )}

        {/* Display generated text if available */}
        {jobDetails.result && (
          <div className="my-6">
            <label
              htmlFor="explanationText"
              className="block text-sm font-medium mb-1 text-slate-200"
            >
              Generated Explanation Text
            </label>
            <Textarea
              id="explanationText"
              value={jobDetails.result}
              readOnly
              rows={10}
              className="w-full text-sm bg-slate-700 border-slate-600 text-slate-50"
            />
          </div>
        )}

        <JobIdDisplay id={jobDetails.job_id} />
        <UpdatesTimeline updates={jobUpdates} title="Generation Timeline" />
        <div className="flex justify-end gap-2 pt-4">
          <Button onClick={onReset} variant="outline">
            Generate Another
          </Button>
          {/* <Button disabled>Share This</Button> */}
        </div>
      </div>
    );
  }

  // Default case: job is processing (this should ideally be covered by page.tsx now)
  // However, if page.tsx's loader is minimal, JobResult can show more details.
  // For now, let's assume page.tsx handles the main "cooking" message for processing states.
  // If jobDetails is available but status is processing, page.tsx shows "cooking..."
  // JobResult can still show the timeline if jobData is available.
  if (
    jobDetails &&
    (jobDetails.status === "pending" ||
      jobDetails.status === "processing" ||
      jobDetails.status === "created")
  ) {
    return (
      <div className="w-full max-w-2xl mx-auto py-4">
        <JobIdDisplay id={jobDetails.job_id} />
        <p className="text-sm text-slate-400 mt-3">
          Status: {jobDetails.status}. Your request is being processed. Please
          be patient.
        </p>
        <UpdatesTimeline updates={jobUpdates} title="Current Progress" />
        <div className="mt-4">
          <Button
            onClick={onReset}
            variant="outline"
            className="w-full"
            disabled={loading}
          >
            {loading ? "Processing..." : "Cancel / Reset"}
          </Button>
        </div>
      </div>
    );
  }

  // Fallback if none of the above conditions are met (e.g. unknown status, or jobData exists but jobDetails doesn't)
  return (
    <div className="w-full max-w-2xl mx-auto py-4 text-center">
      <p className="text-slate-400">Waiting for job information...</p>
      {currentJobId && <JobIdDisplay id={currentJobId} />}
    </div>
  );
}
