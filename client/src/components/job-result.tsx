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
      <Card className="w-full mt-6">
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {updates.length > 0 ? (
            <div className="space-y-1 text-sm px-6 pb-6">
              {updates.map((update, index) => (
                <div
                  key={update.id || index}
                  className="flex items-start p-3 border-b last:border-b-0"
                >
                  <div className="flex-shrink-0 mt-1">
                    {getStatusIcon(update.status)}
                  </div>
                  <div className="flex-grow ml-3">
                    <div className="flex justify-between items-center">
                      <span className="font-medium capitalize">
                        {update.status}
                      </span>
                      <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                        {new Date(update.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </span>
                    </div>
                    {update.message && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {update.message}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center p-6">
              No updates yet...
            </p>
          )}
        </CardContent>
      </Card>
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
        className="text-sm mr-2 whitespace-nowrap font-medium"
      >
        Job ID:
      </label>
      <Input id="jobIdInput" value={id} readOnly className="text-sm" />
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
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Loading...</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <div className="flex items-center justify-center mb-3">
            <Loader size={24} className="mr-2 animate-spin" />
            <p className="text-muted-foreground">Retrieving job details...</p>
          </div>
          <JobIdDisplay id={jobId} />
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="w-full max-w-2xl mx-auto border-destructive">
        <CardHeader>
          <div className="flex items-center text-destructive">
            <AlertCircle size={20} className="mr-2 flex-shrink-0" />
            <CardTitle>Error</CardTitle>
          </div>
          <CardDescription className="text-destructive">
            We encountered a problem retrieving the job details.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive mb-3">{error}</p>
          <JobIdDisplay id={jobId} />
        </CardContent>
        <CardFooter>
          <Button onClick={onReset} variant="outline" className="w-full">
            Try Again
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // Job failed state
  if (jobStatus?.status === "failed" || jobStatus?.status === "error") {
    return (
      <Card className="w-full max-w-2xl mx-auto border-destructive">
        <CardHeader>
          <div className="flex items-center text-destructive">
            <AlertCircle size={20} className="mr-2 flex-shrink-0" />
            <CardTitle>Generation Failed</CardTitle>
          </div>
          <CardDescription className="text-destructive">
            We couldn't generate your explanation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive mb-1">
            Reason: {jobStatus.error || "Unknown error occurred"}
          </p>
          <JobIdDisplay id={jobId} />
          <UpdatesTimeline updates={jobUpdates} title="Attempt Details" />
        </CardContent>
        <CardFooter>
          <Button onClick={onReset} variant="outline" className="w-full mt-4">
            Try Again
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // Job completed successfully
  if (jobStatus?.status === "completed" && jobStatus.result) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <div className="flex items-center text-green-600">
            <CheckCircle size={20} className="mr-2 flex-shrink-0" />
            <CardTitle>Your Explanation is Ready!</CardTitle>
          </div>
          <CardDescription>Explanation generated successfully!</CardDescription>
        </CardHeader>
        <CardContent>
          <JobIdDisplay id={jobId} />

          {/* Video Placeholder - Styled with Tailwind */}
          <div className="my-6 p-4 h-48 flex flex-col items-center justify-center bg-muted/30 border border-dashed rounded-lg">
            <Video size={40} className="text-muted-foreground mb-2" />
            <p className="text-muted-foreground text-sm">
              (Video Playback Area)
            </p>
          </div>

          {/* Result Text using Shadcn Textarea */}
          <div className="mb-6">
            <label
              htmlFor="explanationText"
              className="block text-sm font-medium mb-1"
            >
              Generated Explanation Text
            </label>
            <Textarea
              id="explanationText"
              value={jobStatus.result}
              readOnly
              rows={10}
              className="w-full text-sm bg-background"
            />
          </div>

          <UpdatesTimeline updates={jobUpdates} title="Generation Timeline" />
        </CardContent>
        <CardFooter className="flex justify-end gap-2 pt-4">
          <Button onClick={onReset} variant="outline">
            Generate Another
          </Button>
          <Button disabled>Share This</Button>
        </CardFooter>
      </Card>
    );
  }

  // Default case: job is processing
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center">
          <Loader size={20} className="mr-2 animate-spin" />
          <CardTitle>Working on your explanation</CardTitle>
        </div>
        <CardDescription>
          Status: {jobStatus?.status || job?.status || "Processing..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <JobIdDisplay id={jobId} />
        <p className="text-sm text-muted-foreground mt-3">
          Your request is being processed. Please be patient. This might take a
          few moments.
        </p>
        <UpdatesTimeline updates={jobUpdates} title="Current Progress" />
      </CardContent>
      <CardFooter>
        <Button
          onClick={onReset}
          variant="outline"
          className="w-full"
          disabled={loading}
        >
          {loading ? "Processing..." : "Cancel / Reset"}
        </Button>
      </CardFooter>
    </Card>
  );
}
