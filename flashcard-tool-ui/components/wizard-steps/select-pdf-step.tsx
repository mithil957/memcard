"use client";

import type React from "react";

import { useState, useRef } from "react";
import { FileUp } from "lucide-react";

interface SelectPDFStepProps {
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
}

export default function SelectPDFStep({
  onFileSelect,
  selectedFile,
}: SelectPDFStepProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf") {
        onFileSelect(file);
      } else {
        alert("Please select a PDF file");
      }
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.type === "application/pdf") {
        onFileSelect(file);
      } else {
        alert("Please select a PDF file");
      }
    }
  };

  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="py-4 h-full flex flex-col">
      <h2 className="text-3xl font-semibold mb-0">Select PDF</h2>
      <p className="text-xl font-light mb-4">
        Make sure the PDF contains highlights
      </p>

      <div
        className={`flex-grow border-2 border-dashed rounded-lg p-12 flex flex-col items-center justify-center cursor-pointer ${
          isDragging ? "border-blue-600 bg-blue-50" : "border-gray-300"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          accept=".pdf"
          onChange={handleFileInputChange}
        />

        {selectedFile ? (
          <div className="text-center">
            <FileUp className="w-12 h-12 mx-auto mb-2 text-blue-600" />
            <p className="text-gray-700 mb-2 text-lg">{selectedFile.name}</p>
            <p className="text-gray-500 text-base">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div className="text-center">
            <FileUp className="w-12 h-12 mx-auto mb-2" />
            <p className="text-gray-700 font-normal text-lg">
              Drag & drop here or click to select file
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
