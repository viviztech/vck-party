/**
 * Hierarchy Tree Component
 * Interactive tree visualization of the organizational hierarchy
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ChevronRight, ChevronDown, MapPin, Building2, LayoutGrid, Users } from 'lucide-react';
import { hierarchyService, type HierarchyTreeNode, type HierarchyTreeResponse } from '@/services/hierarchyService';
import { cn } from '@/utils/helpers';

interface TreeNodeProps {
  node: HierarchyTreeNode;
  level: number;
  onNodeClick: (node: HierarchyTreeNode) => void;
  expandedNodes: Set<string>;
  onToggleExpand: (nodeId: string) => void;
}

function TreeNode({ node, level, onNodeClick, expandedNodes, onToggleExpand }: TreeNodeProps) {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedNodes.has(node.id);

  const getLevelIcon = () => {
    switch (node.level) {
      case 'district':
        return <MapPin className="w-4 h-4 text-blue-600" />;
      case 'constituency':
        return <Building2 className="w-4 h-4 text-indigo-600" />;
      case 'ward':
        return <LayoutGrid className="w-4 h-4 text-purple-600" />;
      case 'booth':
        return <Users className="w-4 h-4 text-emerald-600" />;
      default:
        return <MapPin className="w-4 h-4 text-gray-600" />;
    }
  };

  const getLevelColor = () => {
    switch (node.level) {
      case 'district':
        return 'bg-blue-50 border-blue-200';
      case 'constituency':
        return 'bg-indigo-50 border-indigo-200';
      case 'ward':
        return 'bg-purple-50 border-purple-200';
      case 'booth':
        return 'bg-emerald-50 border-emerald-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="select-none">
      <div
        className={cn(
          'flex items-center py-2 px-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors',
          getLevelColor()
        )}
        style={{ marginLeft: `${level * 20}px` }}
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (hasChildren) {
              onToggleExpand(node.id);
            }
          }}
          className={cn(
            'mr-2 p-0.5 rounded hover:bg-gray-200 transition-colors',
            !hasChildren && 'invisible'
          )}
        >
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-600" />
          )}
        </button>
        <div className="mr-2">{getLevelIcon()}</div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 truncate">{node.name}</p>
          <p className="text-xs text-gray-500">{node.code}</p>
        </div>
        {hasChildren && (
          <span className="text-xs text-gray-400 ml-2">
            {isExpanded ? node.children.length : `${node.children.length} items`}
          </span>
        )}
      </div>
      {isExpanded && hasChildren && (
        <div className="mt-1 space-y-1">
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onNodeClick={onNodeClick}
              expandedNodes={expandedNodes}
              onToggleExpand={onToggleExpand}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface HierarchyTreeProps {
  initialExpandedLevel?: number;
  onNodeClick?: (node: HierarchyTreeNode) => void;
  className?: string;
}

export function HierarchyTree({ initialExpandedLevel = 1, onNodeClick, className }: HierarchyTreeProps) {
  const [treeData, setTreeData] = useState<HierarchyTreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');

  const fetchTreeData = useCallback(async () => {
    try {
      setLoading(true);
      const response: HierarchyTreeResponse = await hierarchyService.getHierarchyTree();
      setTreeData(response.districts);
    } catch (err) {
      setError('Failed to load hierarchy tree');
      console.error('Failed to fetch hierarchy tree:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTreeData();
  }, [fetchTreeData]);

  const handleToggleExpand = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  const handleNodeClick = useCallback((node: HierarchyTreeNode) => {
    if (onNodeClick) {
      onNodeClick(node);
    }
    // Auto-expand on click
    if (!expandedNodes.has(node.id)) {
      setExpandedNodes((prev) => new Set([...prev, node.id]));
    }
  }, [onNodeClick, expandedNodes]);

  const filterNodes = useCallback((nodes: HierarchyTreeNode[]): HierarchyTreeNode[] => {
    if (!searchQuery) return nodes;
    
    return nodes
      .map((node) => {
        const matchesSearch = 
          node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          node.code.toLowerCase().includes(searchQuery.toLowerCase());
        
        const filteredChildren = node.children ? filterNodes(node.children) : [];
        
        if (matchesSearch || filteredChildren.length > 0) {
          return { ...node, children: filteredChildren };
        }
        return null;
      })
      .filter(Boolean) as HierarchyTreeNode[];
  }, [searchQuery]);

  if (loading) {
    return (
      <div className={cn('p-4 space-y-3', className)}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse flex items-center py-3 px-3 border rounded-lg">
            <div className="w-4 h-4 bg-gray-200 rounded mr-3" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-1/3" />
              <div className="h-3 bg-gray-200 rounded w-1/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('p-4 text-center text-red-600', className)}>
        {error}
      </div>
    );
  }

  const filteredData = filterNodes(treeData);

  return (
    <div className={cn('space-y-4', className)}>
      <input
        type="text"
        placeholder="Search hierarchy..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
      <div className="space-y-2">
        {filteredData.length === 0 ? (
          <div className="text-center text-gray-500 py-4">
            No results found
          </div>
        ) : (
          filteredData.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              level={0}
              onNodeClick={handleNodeClick}
              expandedNodes={expandedNodes}
              onToggleExpand={handleToggleExpand}
            />
          ))
        )}
      </div>
    </div>
  );
}

export default HierarchyTree;
