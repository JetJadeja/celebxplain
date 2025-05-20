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
  const { job, jobStatus, loading, error } = useJob();
  const params = useParams();

  const jobId = (params.jobId as string) || jobStatus?.job_id || job?.job_id;
  const jobUpdates = job?.updates || [];

  // Loading state
  if (loading && !jobStatus) {
    return (
      <div className="w-full max-w-2xl mx-auto py-4">
        <div className="mb-4">
          <h3 className="text-slate-100 text-xl font-semibold">Loading...</h3>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-3">
            <Loader size={24} className="mr-2 animate-spin text-slate-300" />
            <p className="text-slate-400">Retrieving job details...</p>
          </div>
          <JobIdDisplay id={jobId} />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
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
          <JobIdDisplay id={jobId} />
        </div>
        <div>
          <Button onClick={onReset} variant="outline" className="w-full">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // Job failed state
  if (jobStatus?.status === "failed" || jobStatus?.status === "error") {
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
            Reason: {jobStatus.error || "Unknown error occurred"}
          </p>
          <JobIdDisplay id={jobId} />
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
  if (jobStatus?.status === "completed" && jobStatus.result) {
    return (
      <div className="w-full max-w-2xl mx-auto py-4">
        <div className="mb-4">
          <div className="flex items-center text-green-500">
            <CheckCircle size={20} className="mr-2 flex-shrink-0" />
            <h3 className="text-green-400 text-xl font-semibold">
              Your Explanation is Ready!
            </h3>
          </div>
          <p className="text-slate-300 text-sm mt-1">
            Explanation generated successfully!
          </p>
        </div>
        <div>
          <JobIdDisplay id={jobId} />

          {/* Video Placeholder - Styled with Tailwind */}
          <div className="my-6 p-4 h-48 flex flex-col items-center justify-center bg-slate-700/50 border border-dashed border-slate-600 rounded-lg">
            <Video size={40} className="text-slate-400 mb-2" />
            <p className="text-slate-400 text-sm">(Video Playback Area)</p>
          </div>

          {/* Result Text using Shadcn Textarea */}
          <div className="mb-6">
            <label
              htmlFor="explanationText"
              className="block text-sm font-medium mb-1 text-slate-200"
            >
              Generated Explanation Text
            </label>
            <Textarea
              id="explanationText"
              value={jobStatus.result}
              readOnly
              rows={10}
              className="w-full text-sm bg-slate-700 border-slate-600 text-slate-50"
            />
          </div>
          <UpdatesTimeline updates={jobUpdates} title="Generation Timeline" />
        </div>
        <div className="flex justify-end gap-2 pt-4">
          <Button onClick={onReset} variant="outline">
            Generate Another
          </Button>
          <Button disabled>Share This</Button>
        </div>
      </div>
    );
  }

  // Default case: job is processing
  return (
    <div className="w-full max-w-2xl mx-auto py-4">
      <div className="mb-4">
        <div className="flex items-center">
          <Loader size={20} className="mr-2 animate-spin text-slate-300" />
          <h3 className="text-slate-100 text-xl font-semibold">
            Working on your explanation
          </h3>
        </div>
        <p className="text-slate-300 text-sm mt-1">
          Status: {jobStatus?.status || job?.status || "Processing..."}
        </p>
      </div>
      <div className="mb-4">
        <JobIdDisplay id={jobId} />
        <p className="text-sm text-slate-400 mt-3">
          Your request is being processed. Please be patient. This might take a
          few moments.
        </p>
        <UpdatesTimeline updates={jobUpdates} title="Current Progress" />
      </div>
      <div>
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
