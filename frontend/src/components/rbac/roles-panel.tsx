'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { LoadingState } from '@/components/shared/loading-state';
import { PermissionGate } from '@/components/auth/permission-gate';
import { CreateRoleDialog } from '@/components/rbac/create-role-dialog';
import { useRoles, usePermissionCatalog } from '@/hooks/use-rbac';

export function RolesPanel() {
  const roles = useRoles();
  const permissions = usePermissionCatalog();

  return (
    <Tabs defaultValue="roles">
      <div className="flex items-center justify-between">
        <TabsList>
          <TabsTrigger value="roles">Roles</TabsTrigger>
          <TabsTrigger value="permissions">Permissions</TabsTrigger>
        </TabsList>
        <PermissionGate permission="roles:manage"><CreateRoleDialog /></PermissionGate>
      </div>

      <TabsContent value="roles">
        {roles.isLoading ? <LoadingState label="Loading roles…" /> : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow><TableHead>Role</TableHead><TableHead>Type</TableHead><TableHead>Description</TableHead></TableRow>
                </TableHeader>
                <TableBody>
                  {(roles.data ?? []).map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="font-medium">{r.name}</TableCell>
                      <TableCell><Badge variant={r.is_system ? 'secondary' : 'default'}>{r.is_system ? 'system' : 'custom'}</Badge></TableCell>
                      <TableCell className="text-sm text-muted-foreground">{r.description ?? '—'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </TabsContent>

      <TabsContent value="permissions">
        {permissions.isLoading ? <LoadingState label="Loading permissions…" /> : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow><TableHead>Permission</TableHead><TableHead>Description</TableHead></TableRow>
                </TableHeader>
                <TableBody>
                  {(permissions.data ?? []).map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-mono text-xs">{p.key}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{p.description ?? '—'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </TabsContent>
    </Tabs>
  );
}
