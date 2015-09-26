exception RpcException {
  1: i32  code,
  2: string msg
}

service RpcServiceBase {
    /** 用于rpc client和rpc server连通性和网络延时测试 */
    void ping();
    /** 用于rpc client和rpc proxy的连接测试&网络延时测试 */
    void ping1();
}
