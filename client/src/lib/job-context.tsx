"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useRef,
  useCallback,
} from "react";
import {
  JobCreationResponse,
  FetchedJobData,
  createJob,
  getJobStatus,
} from "./api";

// Define the context state type
interface JobContextState {
  jobData: FetchedJobData | null;
  loading: boolean;
  error: string | null;
  createNewJob: (
    query: string,
    personaId: string
  ) => Promise<JobCreationResponse>;
  clearJob: () => void;
  fetchJobById: (jobId: string) => Promise<FetchedJobData>;
}

// Create context with default values
const JobContext = createContext<JobContextState>({
  jobData: null,
  loading: false,
  error: null,
  createNewJob: async () => {
    throw new Error("JobContext not initialized");
  },
  clearJob: () => {},
  fetchJobById: async () => {
    throw new Error("JobContext not initialized");
  },
});

// Hook for using the job context
export const useJob = () => useContext(JobContext);

interface JobProviderProps {
  children: ReactNode;
}

export const JobProvider = ({ children }: JobProviderProps) => {
  const [jobData, setJobData] = useState<FetchedJobData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lastFetchTime = useRef<{ [jobId: string]: number }>({});
  const isFetching = useRef<{ [jobId: string]: boolean }>({});

  const createNewJob = useCallback(
    async (query: string, personaId: string): Promise<JobCreationResponse> => {
      setLoading(true);
      setError(null);
      setJobData(null);

      try {
        const newJobDetails = await createJob(query, personaId);
        return newJobDetails;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to create job";
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const fetchJobById = useCallback(
    async (jobId: string): Promise<FetchedJobData> => {
      if (isFetching.current[jobId]) {
        return Promise.resolve(
          jobData ||
            ({
              job: {
                job_id: jobId,
                status: "pending",
                created_at: new Date().toISOString(),
              },
              updates: [],
            } as FetchedJobData)
        );
      }

      const now = Date.now();
      const lastFetch = lastFetchTime.current[jobId] || 0;

      if (now - lastFetch < 3000 && jobData && jobData.job.job_id === jobId) {
        return Promise.resolve(jobData);
      }

      isFetching.current[jobId] = true;
      setLoading(true);

      try {
        lastFetchTime.current[jobId] = now;
        const fetchedData = await getJobStatus(jobId);
        setJobData(fetchedData);
        setError(null);
        return fetchedData;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to fetch job";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
        isFetching.current[jobId] = false;
      }
    },
    [jobData]
  );

  const clearJob = useCallback(() => {
    setJobData(null);
    setError(null);
  }, []);

  const value = {
    jobData,
    loading,
    error,
    createNewJob,
    clearJob,
    fetchJobById,
  };

  return <JobContext.Provider value={value}>{children}</JobContext.Provider>;
};
