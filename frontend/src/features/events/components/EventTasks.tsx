/**
 * Event Tasks Component
 * Task management for events
 */

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/DataDisplay/Card';
import { Badge } from '@/components/DataDisplay/Badge';
import { Button } from '@/components/Form/Button';
import { Input } from '@/components/Form/Input';
import { Select } from '@/components/Form/Select';
import { Modal } from '@/components/DataDisplay/Modal';
import type { EventTask, TaskPriority } from '@/services/eventsService';
import { CheckCircle, Circle, Plus, Trash2 } from 'lucide-react';

interface EventTasksProps {
  tasks: EventTask[];
  onAddTask: (data: { title: string; priority: TaskPriority }) => Promise<void>;
  onDeleteTask: (taskId: string) => Promise<void>;
  onCompleteTask: (taskId: string) => Promise<void>;
}

export function EventTasks({ tasks, onAddTask, onDeleteTask, onCompleteTask }: EventTasksProps) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', priority: 'medium' as TaskPriority });

  const getPriorityBadge = (priority: string) => {
    const priorityConfig: Record<string, { variant: 'success' | 'warning' | 'error' | 'default'; label: string }> = {
      low: { variant: 'success', label: 'Low' },
      medium: { variant: 'warning', label: 'Medium' },
      high: { variant: 'error', label: 'High' },
      urgent: { variant: 'error', label: 'Urgent' },
    };
    const config = priorityConfig[priority] || { variant: 'default', label: priority };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const handleAddTask = async () => {
    if (!newTask.title.trim()) return;
    await onAddTask(newTask);
    setNewTask({ title: '', priority: 'medium' });
    setShowAddModal(false);
  };

  const pendingTasks = tasks.filter((t) => t.status !== 'completed');
  const completedTasks = tasks.filter((t) => t.status === 'completed');

  return (
    <Card>
      <div className="flex flex-row items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Tasks</h3>
          <p className="text-sm text-gray-500">{pendingTasks.length} pending | {completedTasks.length} completed</p>
        </div>
        <Button onClick={() => setShowAddModal(true)} leftIcon={<Plus size={16} />}>
          Add Task
        </Button>
      </div>
      <CardContent>
        {tasks.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No tasks yet. Add a task to get started.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {pendingTasks.map((task) => (
              <div key={task.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                <button onClick={() => onCompleteTask(task.id)} className="mt-1 text-gray-400 hover:text-green-500">
                  <Circle size={18} />
                </button>
                <div className="flex-1">
                  <span className="font-medium text-gray-900">{task.title}</span>
                  {getPriorityBadge(task.priority)}
                </div>
                <Button variant="ghost" size="sm" onClick={() => onDeleteTask(task.id)}>
                  <Trash2 size={14} className="text-red-500" />
                </Button>
              </div>
            ))}
            {completedTasks.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-500 mb-2">Completed</h4>
                {completedTasks.map((task) => (
                  <div key={task.id} className="flex items-center space-x-3 p-2 border rounded-lg opacity-60">
                    <CheckCircle size={16} className="text-green-500" />
                    <span className="text-sm text-gray-600 line-through">{task.title}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>

      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add Task">
        <div className="space-y-4">
          <Input
            label="Task Title *"
            value={newTask.title}
            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
            placeholder="Enter task title"
          />
          <Select
            label="Priority"
            value={newTask.priority}
            onChange={(value) => setNewTask({ ...newTask, priority: value as TaskPriority })}
            options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'urgent', label: 'Urgent' },
            ]}
          />
          <div className="flex justify-end space-x-3 pt-4">
            <Button variant="outline" onClick={() => setShowAddModal(false)}>Cancel</Button>
            <Button onClick={handleAddTask} disabled={!newTask.title.trim()}>Add Task</Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
}

export default EventTasks;
