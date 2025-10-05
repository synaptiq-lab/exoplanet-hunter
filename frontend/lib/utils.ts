import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatNumber(value: number, decimals: number = 2): string {
  return value.toFixed(decimals);
}

export function getClassificationColor(classification: string): string {
  switch (classification) {
    case 'CONFIRMED':
      return 'text-green-400';
    case 'CANDIDATE':
      return 'text-yellow-400';
    case 'FALSE POSITIVE':
      return 'text-red-400';
    default:
      return 'text-space-400';
  }
}

export function getClassificationBadgeColor(classification: string): string {
  switch (classification) {
    case 'CONFIRMED':
      return 'bg-green-500/20 text-green-400 border-green-500/50';
    case 'CANDIDATE':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
    case 'FALSE POSITIVE':
      return 'bg-red-500/20 text-red-400 border-red-500/50';
    default:
      return 'bg-space-500/20 text-space-400 border-space-500/50';
  }
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function validateCSVColumns(headers: string[]): { isValid: boolean; missingColumns: string[] } {
  const requiredColumns = [
    'koi_period',
    'koi_duration', 
    'koi_depth',
    'koi_prad'
  ];
  
  const missingColumns = requiredColumns.filter(col => !headers.includes(col));
  
  return {
    isValid: missingColumns.length === 0,
    missingColumns
  };
}

export function downloadCSV(data: any[], filename: string) {
  const csvContent = convertToCSV(data);
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

function convertToCSV(data: any[]): string {
  if (data.length === 0) return '';
  
  const headers = Object.keys(data[0]);
  const csvRows = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value;
      }).join(',')
    )
  ];
  
  return csvRows.join('\n');
}



