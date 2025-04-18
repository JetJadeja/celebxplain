"use client";

import React from "react";
import { GroupBox, Button, TextInput, Frame } from "react95";
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

interface JobResultProps {
  onReset: () => void;
}

// Helper to get status icon
const getStatusIcon = (status?: string) => {
  const lowerStatus = status?.toLowerCase() || "";
  if (lowerStatus.includes("complete"))
    return <CheckCircle size={16} className="mr-2" />;
  if (lowerStatus.includes("fail"))
    return <AlertCircle size={16} className="mr-2 text-red-600" />;
  if (lowerStatus.includes("error"))
    return <AlertCircle size={16} className="mr-2 text-red-600" />;
  if (lowerStatus.includes("processing"))
    return <Loader size={16} className="mr-2 animate-spin-slow" />;
  if (lowerStatus.includes("created"))
    return <FilePlus size={16} className="mr-2" />;
  if (lowerStatus.includes("generating speech"))
    return <MessageSquare size={16} className="mr-2" />;
  if (lowerStatus.includes("generating visuals"))
    return <Clapperboard size={16} className="mr-2" />;
  // Default or other statuses
  return <Loader size={16} className="mr-2 animate-spin-slow" />;
};

// Helper function to render updates timeline (Enhanced)
const UpdatesTimeline = React.memo(
  ({
    updates,
    title = "Job Updates", // Default title
  }: {
    updates: any[];
    title?: string;
  }) => {
    if (!updates || updates.length === 0) return null;

    return (
      <GroupBox label={title} className="w-full mt-4">
        <Frame variant="well" className="p-2 bg-white shadow-inner">
          {updates.length > 0 ? (
            <div className="space-y-1 text-sm">
              {updates.map((update, index) => (
                <div
                  key={update.id || index}
                  className="flex items-start p-1 border-b border-gray-200 last:border-b-0"
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {getStatusIcon(update.status)}
                  </div>
                  <div className="flex-grow">
                    <div className="flex justify-between items-center">
                      <span className="font-medium capitalize">
                        {update.status}
                      </span>
                      <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                        {new Date(update.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </span>
                    </div>
                    <p className="text-xs text-gray-700 mt-0.5">
                      {update.message}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center p-4">
              No updates yet...
            </p>
          )}
        </Frame>
      </GroupBox>
    );
  }
);
UpdatesTimeline.displayName = "UpdatesTimeline";

// Helper function to display job ID (using default TextInput)
const JobIdDisplay = ({ id }: { id?: string }) => {
  if (!id) return null;
  return (
    <div className="flex items-center mt-1">
      <label htmlFor="jobIdInput" className="text-xs mr-2 whitespace-nowrap">
        Job ID:
      </label>
      <TextInput id="jobIdInput" value={id} readOnly fullWidth />
    </div>
  );
};

export function JobResult({ onReset }: JobResultProps) {
  const { job, jobStatus, loading, error } = useJob();
  const params = useParams();

  // Get job ID from route params or job objects
  const jobId = (params.jobId as string) || jobStatus?.job_id || job?.job_id;

  // Extract updates from job object safely
  const jobUpdates = job?.updates || [];

  // --- Render Logic for different states ---

  // If we're loading before a job is created
  if (loading && !jobStatus) {
    return (
      <GroupBox label="Loading..." className="w-full max-w-2xl mx-auto p-4">
        <Frame variant="well" className="p-3 text-center">
          <p className="text-sm">Retrieving job details...</p>
          <JobIdDisplay id={jobId} />
        </Frame>
      </GroupBox>
    );
  }

  // If we encountered an error
  if (error) {
    return (
      <GroupBox
        label="Error"
        className="w-full max-w-2xl mx-auto p-4 border-2 border-red-500 shadow-md"
      >
        <Frame variant="well" className="p-3 mb-3 bg-red-100">
          <div className="flex items-center text-red-800 mb-2">
            <AlertCircle size={18} className="mr-2 flex-shrink-0" />
            <p className="font-semibold">
              We encountered a problem retrieving the job details.
            </p>
          </div>
          <p className="text-sm text-red-700 mb-2">{error}</p>
          <JobIdDisplay id={jobId} />
        </Frame>
        <Button onClick={onReset} fullWidth>
          Try Again
        </Button>
      </GroupBox>
    );
  }

  // If the job failed
  if (jobStatus?.status === "failed" || jobStatus?.status === "error") {
    return (
      <GroupBox
        label="Generation Failed"
        className="w-full max-w-2xl mx-auto p-4 border-2 border-red-500 shadow-md"
      >
        <Frame variant="well" className="p-3 mb-3 bg-red-100">
          <div className="flex items-center text-red-800 mb-2">
            <AlertCircle size={18} className="mr-2 flex-shrink-0" />
            <p className="font-semibold">
              We couldn't generate your explanation.
            </p>
          </div>
          <p className="text-sm text-red-700 mb-2">
            Reason: {jobStatus.error || "Unknown error occurred"}
          </p>
          <JobIdDisplay id={jobId} />
        </Frame>

        <UpdatesTimeline updates={jobUpdates} title="Attempt Details" />
        <Button onClick={onReset} fullWidth className="mt-4">
          Try Again
        </Button>
      </GroupBox>
    );
  }

  // If the job completed successfully
  if (jobStatus?.status === "completed" && jobStatus.result) {
    return (
      <GroupBox
        label="Your Explanation is Ready!"
        className="w-full max-w-2xl mx-auto p-4"
      >
        <Frame variant="well" className="p-3 mb-3 bg-green-100">
          <div className="flex items-center text-green-800 mb-2">
            <CheckCircle size={18} className="mr-2 flex-shrink-0" />
            <p className="font-semibold">Explanation generated successfully!</p>
          </div>
          <JobIdDisplay id={jobId} />
        </Frame>

        {/* Video Placeholder */}
        <Frame
          variant="field"
          className="mb-4 p-4 h-40 flex items-center justify-center bg-gray-200"
        >
          <Video size={40} className="text-gray-500 mr-2" />
          <p className="text-gray-600">(Video Playback Area)</p>
        </Frame>

        {/* Result Text */}
        <GroupBox label="Generated Explanation Text" className="mb-4">
          <Frame variant="well" className="p-1 bg-white">
            <TextInput
              value={jobStatus.result}
              readOnly
              rows={8} // Adjusted rows
              fullWidth
              multiline
            />
          </Frame>
        </GroupBox>

        <UpdatesTimeline updates={jobUpdates} title="Generation Timeline" />
        <Frame className="flex gap-2 mt-4 p-1 justify-end">
          <Button onClick={onReset}>Generate Another</Button>
          <Button disabled>Share This</Button>
        </Frame>
      </GroupBox>
    );
  }

  // Default case: job is processing or being fetched
  return (
    <GroupBox
      label="Working on your explanation"
      className="w-full max-w-2xl mx-auto p-4"
    >
      {/* Status and ID Section - Added w-full */}
      <Frame variant="well" className="p-3 mb-3 w-full">
        <div className="flex items-center mb-2">
          <Loader size={18} className="mr-2 animate-spin-slow" />
          <span className="font-semibold">
            Status: {jobStatus?.status || job?.status || "Processing"}
          </span>
        </div>
        <JobIdDisplay id={jobId} />
        <p className="text-xs text-gray-600 mt-2">
          Your request is being processed. Please be patient.
        </p>
      </Frame>

      {/* Updates Timeline */}
      <UpdatesTimeline updates={jobUpdates} />
    </GroupBox>
  );
}
