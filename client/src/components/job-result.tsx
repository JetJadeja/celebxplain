"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useJob } from "@/lib/job-context";
import { useParams } from "next/navigation";

interface JobResultProps {
  onReset: () => void;
}

export function JobResult({ onReset }: JobResultProps) {
  const { job, jobStatus, loading, error } = useJob();
  const params = useParams();

  // Get job ID from route params or job objects
  const jobId = (params.jobId as string) || jobStatus?.job_id || job?.job_id;

  // Helper function to display job ID
  const JobIdDisplay = ({ id }: { id?: string }) => {
    if (!id) return null;
    return (
      <span className="block mt-1 text-xs">
        Job ID: <span className="font-mono">{id}</span>
      </span>
    );
  };

  // If we're loading before a job is created
  if (loading && !jobStatus) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Loading your explanation...</CardTitle>
          <CardDescription>
            This might take a moment. We're retrieving your explanation.
            <JobIdDisplay id={jobId} />
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4" />
          <p className="text-muted-foreground text-center">
            Please wait while we load your request.
          </p>
        </CardContent>
      </Card>
    );
  }

  // If we encountered an error
  if (error) {
    return (
      <Card className="w-full max-w-2xl mx-auto border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">Error</CardTitle>
          <CardDescription>
            We encountered a problem with your explanation
            <JobIdDisplay id={jobId} />
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error}</p>
        </CardContent>
        <CardFooter>
          <Button onClick={onReset} variant="outline" className="w-full">
            Try Again
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // If the job failed
  if (jobStatus?.status === "failed") {
    return (
      <Card className="w-full max-w-2xl mx-auto border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">Generation Failed</CardTitle>
          <CardDescription>
            We couldn't generate your explanation
            <JobIdDisplay id={jobId} />
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">
            {jobStatus.error || "Unknown error occurred"}
          </p>
        </CardContent>
        <CardFooter>
          <Button onClick={onReset} variant="outline" className="w-full">
            Try Again
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // If the job completed successfully
  if (jobStatus?.status === "completed" && jobStatus.result) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Your Explanation is Ready!</CardTitle>
          <CardDescription>
            Here's your celebrity explanation
            <JobIdDisplay id={jobId} />
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="aspect-video bg-black/10 rounded-md flex items-center justify-center mb-4">
            <p className="text-muted-foreground">Video would display here</p>
          </div>
          <div className="bg-primary/5 p-4 rounded-md">
            <p className="whitespace-pre-line">{jobStatus.result}</p>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button onClick={onReset} variant="outline" className="flex-1">
            Generate Another
          </Button>
          <Button variant="default" className="flex-1">
            Share This
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // Default case: job is processing or being fetched
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Working on your explanation</CardTitle>
        <CardDescription>
          Status: {jobStatus?.status || job?.status || "Processing"}
          <JobIdDisplay id={jobId} />
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4" />
        <p className="text-muted-foreground text-center">
          Your request is being processed. This may take a minute.
        </p>
      </CardContent>
    </Card>
  );
}
