"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChevronLeft, Loader2 } from "lucide-react";
import { pb } from "@/lib/pocketbase";
import { useToast } from "@/hooks/use-toast";
import type { RecordModel } from "pocketbase";

interface Job {
  id: string;
  pdfName: string;
  status: string;
  submittedAt: string;
  cardId: string | null;
}

interface JobRecord extends RecordModel {
  user: string;
  status: string;
  created: string;
  source_pdf: string;
  expand?: {
    source_pdf?: {
      original_filename?: string;
    };
  };
}

export default function JobStatusPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const formatJobRecord = useCallback((record: JobRecord): Job => {
    let pdfName = "N/A";
    if (record.expand && record.expand.source_pdf) {
      pdfName = record.expand.source_pdf.original_filename || "Unnamed PDF";
    }
    return {
      id: record.id,
      pdfName: pdfName,
      status: record.status || "Unknown",
      submittedAt: record.created
        ? new Date(record.created).toLocaleString()
        : "N/A",
      cardId: record.status === "Finished" ? record.id : null,
    };
  }, []);

  useEffect(() => {
    const fetchJobs = async () => {
      if (!pb.authStore.isValid || !pb.authStore.model?.id) {
        toast({
          title: "Authentication Error",
          description: "You need to be logged in to view job statuses.",
          variant: "destructive",
        });
        router.push("/auth");
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      setError(null);

      try {
        const records = await pb
          .collection("job_requests")
          .getFullList<JobRecord>({
            sort: "-created",
            filter: `user = "${pb.authStore.model.id}"`,
            expand: "source_pdf",
            requestKey: null,
          });
        setJobs(records.map(formatJobRecord));
      } catch (err: any) {
        console.error("Failed to fetch jobs:", err);
        setError("Failed to load job statuses. Please try again later.");
        toast({
          title: "Error Fetching Jobs",
          description: err.message || "Could not retrieve job statuses.",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchJobs();

    const unsubscribe = pb.collection("job_requests").subscribe<JobRecord>(
      "*", // Subscribe to all actions
      async (e) => {
        if (!pb.authStore.model || e.record.user !== pb.authStore.model.id) {
          return;
        }

        let fullRecord = e.record;
        if (
          (e.action === "create" || e.action === "update") &&
          !fullRecord.expand?.source_pdf
        ) {
          try {
            fullRecord = await pb
              .collection("job_requests")
              .getOne<JobRecord>(e.record.id, {
                expand: "source_pdf",
                requestKey: null,
              });
          } catch (fetchErr) {
            console.error(
              "Error fetching full record for subscription event:",
              fetchErr,
            );
            return; // Skip update if we can't get full data
          }
        }

        const formattedJob = formatJobRecord(fullRecord);

        setJobs((prevJobs) => {
          if (e.action === "create") {
            if (prevJobs.find((job) => job.id === formattedJob.id)) {
              return prevJobs.map((job) =>
                job.id === formattedJob.id ? formattedJob : job,
              );
            }
            return [formattedJob, ...prevJobs].sort(
              (a, b) =>
                new Date(b.submittedAt).getTime() -
                new Date(a.submittedAt).getTime(),
            );
          }
          if (e.action === "update") {
            return prevJobs.map((job) =>
              job.id === formattedJob.id ? formattedJob : job,
            );
          }
          if (e.action === "delete") {
            return prevJobs.filter((job) => job.id !== e.record.id);
          }
          return prevJobs;
        });
      },
    );

    return () => {
      try {
        pb.collection("job_requests").unsubscribe();
      } catch (unsubError) {
        console.error("Error unsubscribing:", unsubError);
      }
    };
  }, [router, toast, formatJobRecord]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Finished":
        return "text-green-600";
      case "Error":
        return "text-red-600";
      default:
        return "text-blue-600";
    }
  };

  const handleViewCards = (cardId: string) => {
    router.push(`/wizard/rate-cards/${cardId}`);
  };

  const handleBack = () => {
    router.push("/actions");
  };

  if (isLoading && jobs.length === 0) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
        <Card className="w-full max-w-4xl bg-white rounded-3xl shadow-lg p-6 text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold">Loading job statuses...</h2>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
        <Card className="w-full max-w-4xl bg-white rounded-3xl shadow-lg p-6 text-center">
          <h2 className="text-2xl font-semibold text-red-600 mb-4">Error</h2>
          <p className="mb-6">{error}</p>
          <Button onClick={handleBack}>Go Back</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl bg-white rounded-3xl shadow-lg overflow-hidden">
        <div className="p-6">
          <h1 className="text-3xl font-semibold mb-6">
            Flashcard Creation Jobs
          </h1>

          {jobs.length === 0 && !isLoading ? (
            <div className="text-center py-10">
              <p className="text-xl text-gray-500">No jobs found.</p>
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden mb-6">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50">
                    <TableHead className="font-bold">Job ID</TableHead>
                    <TableHead className="font-bold">PDF Name</TableHead>
                    <TableHead className="font-bold">Status</TableHead>
                    <TableHead className="font-bold">Submitted At</TableHead>
                    <TableHead className="font-bold">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.id} className="border-t">
                      <TableCell className="truncate max-w-xs">
                        {job.id}
                      </TableCell>
                      <TableCell className="truncate max-w-xs">
                        {job.pdfName}
                      </TableCell>
                      <TableCell
                        className={`${getStatusColor(job.status)} font-medium`}
                      >
                        {job.status}
                      </TableCell>
                      <TableCell className="">{job.submittedAt}</TableCell>
                      <TableCell className="">
                        {job.status === "Finished" && job.cardId ? (
                          <Button
                            variant="link"
                            className="p-0 h-auto text-blue-600 hover:underline"
                            onClick={() => handleViewCards(job.cardId!)}
                          >
                            View Cards
                          </Button>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          <Button
            variant="ghost"
            className="flex items-center gap-1 px-0 hover:bg-transparent hover:text-blue-700"
            onClick={handleBack}
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
        </div>
      </Card>
    </div>
  );
}
